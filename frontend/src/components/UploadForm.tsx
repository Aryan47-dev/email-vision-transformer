import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";

interface UploadFormProps {
  onSubmit: (file: File) => void;
  isLoading: boolean;
}

function UploadForm({ onSubmit, isLoading }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (file) {
      onSubmit(file);
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <input type="file" accept="image/*" onChange={handleFileChange} disabled={isLoading} />
      <button type="submit" disabled={!file || isLoading}>
        {isLoading ? "Generating…" : "Generate Email HTML"}
      </button>
    </form>
  );
}

export default UploadForm;
