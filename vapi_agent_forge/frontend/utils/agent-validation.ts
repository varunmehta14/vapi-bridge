interface AgentConfig {
  name: string;
  description: string;
  tools: Array<{
    name: string;
    description: string;
    parameters: Array<{
      name: string;
      type: string;
      required: boolean;
      description?: string;
    }>;
  }>;
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export function validateAgentConfig(config: any): ValidationResult {
  const errors: string[] = [];

  // Validate top-level fields
  if (!config.name || typeof config.name !== 'string') {
    errors.push('Agent name is required and must be a string');
  }

  if (!config.description || typeof config.description !== 'string') {
    errors.push('Agent description is required and must be a string');
  }

  // Validate tools array
  if (!Array.isArray(config.tools)) {
    errors.push('Tools must be an array');
  } else {
    config.tools.forEach((tool: any, index: number) => {
      // Validate tool name
      if (!tool.name || typeof tool.name !== 'string') {
        errors.push(`Tool at index ${index} must have a name string`);
      }

      // Validate tool description
      if (!tool.description || typeof tool.description !== 'string') {
        errors.push(`Tool at index ${index} must have a description string`);
      }

      // Validate parameters array
      if (!Array.isArray(tool.parameters)) {
        errors.push(`Tool "${tool.name}" must have a parameters array`);
      } else {
        tool.parameters.forEach((param: any, paramIndex: number) => {
          // Validate parameter name
          if (!param.name || typeof param.name !== 'string') {
            errors.push(`Parameter at index ${paramIndex} in tool "${tool.name}" must have a name string`);
          }

          // Validate parameter type
          if (!param.type || typeof param.type !== 'string') {
            errors.push(`Parameter "${param.name}" in tool "${tool.name}" must have a type string`);
          }

          // Validate required flag
          if (typeof param.required !== 'boolean') {
            errors.push(`Parameter "${param.name}" in tool "${tool.name}" must have a required boolean flag`);
          }

          // Validate optional description
          if (param.description && typeof param.description !== 'string') {
            errors.push(`Parameter "${param.name}" in tool "${tool.name}" description must be a string`);
          }
        });
      }
    });
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
} 