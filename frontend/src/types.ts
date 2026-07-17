export type BlockType =
  | "header"
  | "paragraph"
  | "image"
  | "button"
  | "footer"
  | "hero"
  | "divider"
  | "other";

export interface BoundingBox {
  ymin: number;
  xmin: number;
  ymax: number;
  xmax: number;
}

export interface LayoutBlock {
  type: BlockType;
  box: BoundingBox;
  text: string;
}

export interface LayoutExtractionResult {
  blocks: LayoutBlock[];
  degraded: boolean;
  model: string;
}

export type ColorStyleSource = "gemini" | "local_fallback";

export interface ColorStyleResult {
  bg_color: string;
  heading_color: string;
  link_color: string;
  heading_font: string;
  body_font: string;
  body_font_size: string;
  degraded: boolean;
  source: ColorStyleSource;
}

export interface HtmlAssemblyResult {
  html: string;
}
