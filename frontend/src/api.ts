import axios from "axios";
import type { ColorStyleResult, HtmlAssemblyResult, LayoutExtractionResult } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const client = axios.create({ baseURL: API_BASE_URL });

export async function extractLayout(file: File): Promise<LayoutExtractionResult> {
  const formData = new FormData();
  formData.append("image", file);
  const response = await client.post<LayoutExtractionResult>(
    "/api/layout-extraction",
    formData
  );
  return response.data;
}

export async function extractColorStyle(file: File): Promise<ColorStyleResult> {
  const formData = new FormData();
  formData.append("image", file);
  const response = await client.post<ColorStyleResult>("/api/color-style", formData);
  return response.data;
}

export async function assembleHtml(
  layout: LayoutExtractionResult,
  styles: ColorStyleResult
): Promise<HtmlAssemblyResult> {
  const response = await client.post<HtmlAssemblyResult>("/api/html-assembly", {
    layout,
    styles,
  });
  return response.data;
}
