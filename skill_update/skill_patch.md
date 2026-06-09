# Skill Patch — xray_grounding_tool

## Tool Selection Logic

| Context | Action |
|---|---|
| Source type is `image` (JPG/PNG) | Auto-run `xray_grounding_tool` on upload |
| User mentions "x-ray", "xray", "chest", "cxr", "radiology" | Route to `xray_grounding_tool` |
| User asks to "analyze", "review", "detect", or "ground" an image | Route to `xray_grounding_tool` |
| Source type is DICOM | Use `dicom_review_tool` first, then offer `xray_grounding_tool` if abnormal |

## Skill Patch Description

Add `xray_grounding_tool` to the ChatClinic modality router for `medical-image` source type.

When an image source is uploaded and identified as a chest X-ray (PNG/JPG):
1. Auto-trigger `xray_grounding_tool` as the primary analysis tool.
2. Return structured JSON including `abnormal`, `impression`, `findings`, and `bounding_boxes`.
3. If `abnormal=true`, render annotated image with bounding boxes in the Studio viewer.
4. Allow follow-up chat questions about specific findings.

## Integration Points

- **Entrypoint**: `plugins.xray_grounding_tool.logic:execute`
- **Result slot**: `xray_grounding_result`
- **Studio renderer**: `image_review` (existing renderer, shows annotated output)
- **Chat response kind**: `image_chat`
