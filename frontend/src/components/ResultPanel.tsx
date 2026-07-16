import { useEffect, useState } from "react";

interface ResultPanelProps {
  html: string;
}

function ResultPanel({ html }: ResultPanelProps) {
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  useEffect(() => {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    setDownloadUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [html]);

  return (
    <div className="panel">
      <h2>Generated Email HTML</h2>
      <iframe
        className="result-frame"
        title="Generated email preview"
        srcDoc={html}
        sandbox="allow-same-origin"
      />
      {downloadUrl && (
        <a className="download-link" href={downloadUrl} download="email.html">
          Download .html
        </a>
      )}
      <details className="raw-html">
        <summary>View raw HTML</summary>
        <pre>{html}</pre>
      </details>
    </div>
  );
}

export default ResultPanel;
