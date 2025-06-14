import React, { useState, useEffect } from 'react';
import MonacoEditor from '@monaco-editor/react';
import { parse } from 'yaml';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { AlertCircle } from 'lucide-react';

interface YamlEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: string;
  readOnly?: boolean;
}

const YamlEditor: React.FC<YamlEditorProps> = ({
  value,
  onChange,
  height = '500px',
  readOnly = false
}) => {
  const [error, setError] = useState<string | null>(null);

  const validateYaml = (yamlString: string) => {
    try {
      parse(yamlString);
      setError(null);
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Invalid YAML');
      return false;
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value) {
      validateYaml(value);
      onChange(value);
    }
  };

  useEffect(() => {
    validateYaml(value);
  }, [value]);

  return (
    <div className="w-full">
      <MonacoEditor
        height={height}
        defaultLanguage="yaml"
        value={value}
        onChange={handleEditorChange}
        options={{
          minimap: { enabled: false },
          readOnly,
          lineNumbers: 'on',
          roundedSelection: false,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 2,
          wordWrap: 'on',
        }}
        theme="vs-dark"
      />
      {error && (
        <Alert variant="destructive" className="mt-2">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>YAML Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default YamlEditor; 