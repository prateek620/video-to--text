# Updated Services

## Speech to Text
* Replace placeholder summarization pipeline with real extraction and richer document generation.
* Update `backend/app/services/speech_to_text.py` to utilize Whisper transcription from extracted audio and return real timestamped `TranscriptSegments` with robust error handling and fallback only when transcription yields nothing.

## OCR Processing
* Update `backend/app/services/ocr_processing.py` to run Tesseract OCR over extracted frames.
* Return timestamp-aligned `FrameText` entries instead of `SAMPLE_OCR`.

## Frame Analysis
* Update `backend/app/services/frame_analysis.py` to perform real frame extraction.
* Implement scene detection using OpenCV timestamps rather than `SAMPLE_SCENES`.

## Knowledge Builder
* Enhance `backend/app/services/knowledge_builder.py` to build detailed chapter paragraphs from broader segment windows.
* Improve chapter title generation, aggregate key takeaways, questions, flashcards, and knowledge graphs from real content.
* Add guardrails to avoid generic placeholders like 'topic/objectives/95% accuracy' unless present in the source text.

## Testing
* Add/test updates in `backend/tests` to validate non-placeholder generation behavior.
* Ensure that generated markdown reflects transcript content with meaningful sections.

## Code Safety
* Ensure code is production-safe.
* Remove hardcoded `SAMPLE_*` stubs used as primary outputs.