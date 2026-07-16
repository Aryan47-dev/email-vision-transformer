import { useEffect, useState } from "react";

interface ImagePreviewProps {
  file: File;
}

function ImagePreview({ file }: ImagePreviewProps) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setObjectUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  if (!objectUrl) {
    return null;
  }

  return (
    <div className="panel">
      <h2>Original Screenshot</h2>
      <img className="preview-image" src={objectUrl} alt="Uploaded email screenshot" />
    </div>
  );
}

export default ImagePreview;
