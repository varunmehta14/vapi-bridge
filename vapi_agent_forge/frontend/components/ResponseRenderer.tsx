import React from 'react';
import { JsonView, allExpanded, darkStyles, defaultStyles } from 'react-json-view-lite';
import 'react-json-view-lite/dist/index.css';

interface ResponseRendererProps {
  data: any;
  type?: 'json' | 'table' | 'text' | 'auto';
  theme?: 'light' | 'dark';
}

const ResponseRenderer: React.FC<ResponseRendererProps> = ({ 
  data, 
  type = 'auto',
  theme = 'light' 
}) => {
  const detectType = (data: any): 'json' | 'table' | 'text' => {
    if (Array.isArray(data)) return 'table';
    if (typeof data === 'object' && data !== null) return 'json';
    return 'text';
  };

  const renderType = type === 'auto' ? detectType(data) : type;

  const renderContent = () => {
    switch (renderType) {
      case 'json':
        return (
          <div className="rounded-lg overflow-hidden">
            <JsonView 
              data={data} 
              shouldExpandNode={allExpanded}
              style={theme === 'dark' ? darkStyles : defaultStyles}
            />
          </div>
        );
      
      case 'table':
        if (!Array.isArray(data)) return <div>Invalid table data</div>;
        const headers = Object.keys(data[0] || {});
        return (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {headers.map(header => (
                    <th key={header} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.map((row, i) => (
                  <tr key={i}>
                    {headers.map(header => (
                      <td key={header} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {typeof row[header] === 'object' 
                          ? JSON.stringify(row[header])
                          : String(row[header])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      
      case 'text':
        return (
          <div className="p-4 bg-white rounded-lg shadow">
            <pre className="whitespace-pre-wrap">{String(data)}</pre>
          </div>
        );
      
      default:
        return <div>Unsupported data type</div>;
    }
  };

  return (
    <div className="w-full">
      {renderContent()}
    </div>
  );
};

export default ResponseRenderer; 