import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { config } = body

    if (!config) {
      return NextResponse.json(
        { error: 'Configuration is required' },
        { status: 400 }
      )
    }

    // Simple YAML validation without external dependencies
    const validateYamlStructure = (yamlString: string) => {
      const lines = yamlString.split('\n')
      const errors: string[] = []
      
      // Check for basic YAML structure
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i]
        if (line.trim() === '') continue
        
        // Check for proper indentation (should be spaces, not tabs)
        if (line.match(/^\t/)) {
          errors.push(`Line ${i + 1}: Use spaces instead of tabs for indentation`)
        }
        
        // Check for unmatched quotes
        const singleQuotes = (line.match(/'/g) || []).length
        const doubleQuotes = (line.match(/"/g) || []).length
        
        if (singleQuotes % 2 !== 0) {
          errors.push(`Line ${i + 1}: Unmatched single quote`)
        }
        if (doubleQuotes % 2 !== 0) {
          errors.push(`Line ${i + 1}: Unmatched double quote`)
        }
      }
      
      return errors
    }

    const validationErrors = validateYamlStructure(config)
    
    if (validationErrors.length > 0) {
      return NextResponse.json({
        success: false,
        message: 'Configuration has validation errors',
        errors: validationErrors,
        suggestions: [
          'Ensure proper indentation using spaces (not tabs)',
          'Check for unmatched quotes',
          'Verify YAML syntax is correct'
        ]
      }, { status: 400 })
    }

    // Extract key information from the configuration
    const configLines = config.split('\n')
    const configInfo: Record<string, any> = {}
    
    // Smart extraction for both flat and nested structures
    configLines.forEach((line: string) => {
      const trimmedLine = line.trim()
      
      // Handle nested assistant structure
      if (trimmedLine.includes('name:') && !trimmedLine.startsWith('#')) {
        const value = trimmedLine.split('name:')[1]?.trim().replace(/["']/g, '')
        if (value) configInfo.name = value
      }
      
      if (trimmedLine.includes('model:') && !trimmedLine.startsWith('#')) {
        const value = trimmedLine.split('model:')[1]?.trim().replace(/["']/g, '')
        if (value && !value.includes('{') && !value.includes('[')) {
          configInfo.model = value
        }
      }
      
      if (trimmedLine.includes('provider:') && !trimmedLine.startsWith('#')) {
        const value = trimmedLine.split('provider:')[1]?.trim().replace(/["']/g, '')
        if (value) {
          if (trimmedLine.includes('voice')) {
            configInfo.voiceProvider = value
          } else {
            configInfo.modelProvider = value
          }
        }
      }
      
      if (trimmedLine.includes('serverUrl:') || trimmedLine.includes('server_url:')) {
        const value = trimmedLine.split(/serverUrl:|server_url:/)[1]?.trim().replace(/["']/g, '')
        if (value) configInfo.serverUrl = value
      }
      
      if (trimmedLine.includes('system_prompt_template:') || trimmedLine.includes('systemMessage:')) {
        configInfo.hasSystemPrompt = true
      }
      
      if (trimmedLine.includes('firstMessage:')) {
        const value = trimmedLine.split('firstMessage:')[1]?.trim().replace(/["']/g, '')
        if (value) configInfo.firstMessage = value
      }
    })

    // Count tools (look for tool definitions)
    const toolCount = (config.match(/- name:/g) || []).length
    
    // Detect structure type
    const hasAssistantSection = config.includes('assistant:')
    const hasTopLevelName = config.match(/^name:/m)
    const structureType = hasAssistantSection ? 'assistant-nested' : hasTopLevelName ? 'flat' : 'unknown'

    // Generate intelligent suggestions
    const suggestions: string[] = []
    
    if (toolCount === 0) {
      suggestions.push('Consider adding tools to make your agent more capable')
    } else {
      suggestions.push(`Found ${toolCount} tools configured - great!`)
    }
    
    if (!configInfo.serverUrl) {
      suggestions.push('Add a serverUrl for webhook functionality')
    } else {
      suggestions.push('Server URL configured ✓')
    }
    
    if (!configInfo.voiceProvider) {
      suggestions.push('Configure voice settings for better user experience')
    } else {
      suggestions.push(`Voice provider: ${configInfo.voiceProvider} ✓`)
    }
    
    if (!configInfo.hasSystemPrompt) {
      suggestions.push('Add a system prompt or system_prompt_template')
    } else {
      suggestions.push('System prompt configured ✓')
    }
    
    if (!configInfo.firstMessage) {
      suggestions.push('Consider adding a firstMessage for better user experience')
    } else {
      suggestions.push('First message configured ✓')
    }

    return NextResponse.json({
      success: true,
      message: 'Configuration validation successful',
      validation: {
        syntaxValid: true,
        structureType,
        configInfo,
        toolCount,
        lineCount: configLines.length,
        estimatedTokens: config.length / 4, // Rough estimate
        hasNestedStructure: hasAssistantSection,
        detectedFields: Object.keys(configInfo)
      },
      suggestions
    })

  } catch (error) {
    console.error('Error testing agent configuration:', error)
    return NextResponse.json(
      { 
        success: false,
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
} 