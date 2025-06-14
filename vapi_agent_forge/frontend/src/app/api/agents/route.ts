import { NextRequest, NextResponse } from 'next/server'
import * as yaml from 'js-yaml'

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

    // Validate YAML syntax
    try {
      const parsed = yaml.load(config)
      
      // Basic validation for required fields
      if (!parsed || typeof parsed !== 'object') {
        throw new Error('Invalid configuration structure')
      }

      const parsedConfig = parsed as Record<string, any>
      
      // Handle different YAML structures
      let configToValidate = parsedConfig
      let configType = 'unknown'
      
      // Check if it's a nested structure under 'assistant'
      if (parsedConfig.assistant && typeof parsedConfig.assistant === 'object') {
        configToValidate = parsedConfig.assistant
        configType = 'assistant-nested'
      }
      // Check if it's a flat structure
      else if (parsedConfig.name || parsedConfig.model || parsedConfig.systemMessage) {
        configType = 'flat'
      }
      
      // Flexible validation based on structure
      const missingFields: string[] = []
      
      // Check for name (required)
      if (!configToValidate.name) {
        missingFields.push('name')
      }
      
      // Check for model (can be string or object)
      if (!configToValidate.model) {
        missingFields.push('model')
      }
      
      // Check for system message (various possible field names)
      const systemMessageFields = ['systemMessage', 'system_prompt_template', 'systemPrompt']
      const hasSystemMessage = systemMessageFields.some(field => 
        configToValidate[field] || 
        (configToValidate.model && typeof configToValidate.model === 'object' && configToValidate.model[field])
      )
      
      if (!hasSystemMessage) {
        missingFields.push('systemMessage (or system_prompt_template)')
      }
      
      if (missingFields.length > 0) {
        return NextResponse.json(
          { 
            error: 'Missing required fields',
            missingFields,
            suggestion: `Please ensure your configuration includes: ${missingFields.join(', ')}`,
            detectedStructure: configType,
            parsedStructure: {
              hasAssistant: !!parsedConfig.assistant,
              hasName: !!configToValidate.name,
              hasModel: !!configToValidate.model,
              modelType: typeof configToValidate.model,
              availableFields: Object.keys(configToValidate)
            }
          },
          { status: 400 }
        )
      }

      // Extract configuration stats
      const toolCount = Array.isArray(parsedConfig.tools) ? parsedConfig.tools.length : 
                       Array.isArray(configToValidate.tools) ? configToValidate.tools.length : 0
      
      const hasVoice = !!(parsedConfig.voice || configToValidate.voice)
      const hasServerUrl = !!(parsedConfig.serverUrl || configToValidate.serverUrl)

      // Return success with detailed analysis
      return NextResponse.json({
        success: true,
        message: 'Agent configuration saved successfully',
        parsedConfig,
        configType,
        timestamp: new Date().toISOString(),
        configStats: {
          hasVoice,
          toolCount,
          hasServerUrl,
          structure: configType,
          agentName: configToValidate.name,
          modelInfo: configToValidate.model
        }
      })

    } catch (yamlError) {
      return NextResponse.json(
        { 
          error: 'Invalid YAML syntax',
          details: yamlError instanceof Error ? yamlError.message : 'Unknown YAML error',
          suggestion: 'Please check your YAML formatting. Common issues: incorrect indentation, missing quotes, or invalid characters.'
        },
        { status: 400 }
      )
    }

  } catch (error) {
    console.error('Error processing agent configuration:', error)
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
} 