import { useState } from "react";
import axios from "axios";
import UploadForm from "./components/UploadForm";
import ImagePreview from "./components/ImagePreview";
import ResultPanel from "./components/ResultPanel";
import { assembleHtml, extractColorStyle, extractLayout } from "./api";

type Status = "idle" | "analyzing-layout" | "analyzing-style" | "assembling" | "done" | "error";

const STATUS_MESSAGES: Record<Status, string> = {
  idle: "",
  "analyzing-layout": "Analyzing layout…",
  "analyzing-style": "Analyzing colors and fonts…",
  assembling: "Assembling HTML…",
  done: "Done.",
  error: "Something went wrong.",
};

function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unknown error";
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [html, setHtml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(selectedFile: File) {
    setFile(selectedFile);
    setHtml(null);
    setError(null);

    try {
      setStatus("analyzing-layout");
      const layout = await extractLayout(selectedFile);

      setStatus("analyzing-style");
      const styles = await extractColorStyle(selectedFile);

      setStatus("assembling");
      const result = await assembleHtml(layout, styles);

      setHtml(result.html);
      setStatus("done");
    } catch (err) {
      setError(extractErrorMessage(err));
      setStatus("error");
    }
  }

  const isLoading = status !== "idle" && status !== "done" && status !== "error";

  return (
    <div className="app">
      <h1>Email Vision Transformer</h1>
      <p className="subtitle">
        Upload an email design screenshot to generate a pixel-accurate HTML email.
      </p>

      <UploadForm onSubmit={handleSubmit} isLoading={isLoading} />

      {status !== "idle" && status !== "error" && <p className="status">{STATUS_MESSAGES[status]}</p>}
      {error && <p className="error">{error}</p>}

      <div className="results">
        {file && <ImagePreview file={file} />}
        {html && <ResultPanel html={html} />}
      </div>
    </div>
  );
}

export default App;
