# Architecture Decision Records (ADR)

---

## ADR 001: Choice of Language and Frameworks

* **Status**: Accepted

* **Context**:  
  The tool needs to run inside Autodesk Maya, provide a UI, and support automated testing.

* **Decision**:  
  - Use **Python 3.9** for scripting, matching Maya’s embedded interpreter.  
  - Use **PySide2** (Qt) for UI components, ensuring native Maya integration.  
  - Use **pytest** with mocking for automated unit and UI tests.

* **Consequences**:  
  - Seamless integration inside Maya and automated testing outside Maya (via mocks).  
  - Easier maintenance and community support.

---

## ADR 002: Asset Collection & Deduplication

* **Status**: Accepted

* **Context**:  
  Asset directories may contain multiple file formats with the same logical asset base name.

* **Decision**:  
  - Implement a prioritized asset file collector that picks one file per base name, preferring certain extensions (`.ma`, `.mb`, `.usd`, etc.).

* **Consequences**:  
  - Avoids duplicate imports.  
  - Simplifies user expectations and internal naming logic.

---

## ADR 003: Collision-Resilient Renaming

* **Status**: Accepted

* **Context**:  
  Maya scene nodes require unique names to avoid conflicts; imported assets might share names.

* **Decision**:  
  - Apply sanitized naming prefixes and append numeric suffixes (`_001`, `_002`, ...) to ensure unique names.  
  - Collision safety applies during preview and actual import.

* **Consequences**:  
  - Prevents naming conflicts at runtime.  
  - Slightly more complex logic for name generation.

---

## ADR 004: Batch vs. Single Path Repair

* **Status**: Accepted

* **Context**:  
  Users need to fix broken file paths both automatically during batch import and manually on demand.

* **Decision**:  
  - Provide an option for automatic path repair during batch import.  
  - Also offer a separate Batch Path Repair button to fix paths without re-importing.

* **Consequences**:  
  - More flexible workflows for artists.  
  - Reduces friction in fixing references and textures.

---

## ADR 005: Progress Reporting

* **Status**: Accepted

* **Context**:  
  Long-running batch import and cleanup processes require user feedback.

* **Decision**:  
  - Integrate a progress bar updated via callbacks from batch operations.  
  - Progress bar shown in UI and resets after completion.

* **Consequences**:  
  - Improved user experience with visible feedback during imports.

---

## ADR 006: Custom Naming Prefix

* **Status**: Accepted

* **Context**:  
  Artists require flexibility to customize naming conventions per project or asset batch.

* **Decision**:  
  - Add a UI checkbox and text input for enabling naming and specifying prefix dynamically.  
  - Prefix applied in preview and batch import steps.

* **Consequences**:  
  - Enables project- or user-specific naming schemes.  
  - Avoids hardcoded prefixes.

---

## ADR 007: Interactive Scaling Slider

* **Status**: Accepted

* **Context**:  
  Users want to adjust the scale of imported assets easily within the tool.

* **Decision**:  
  - Add a horizontal slider (50%-150%) to scale selected Maya nodes interactively.  
  - Resets when selection changes.

* **Consequences**:  
  - Provides intuitive and immediate scaling control.  
  - Enhances the tool’s flexibility and user-friendliness.

---

## ADR 008: USD Export and Variant Browsing

* **Status**: Accepted

* **Context**:  
  The pipeline must support exporting Maya selections as USD files and manipulating USD variants.

* **Decision**:  
  - Implement Export Selection to USD functionality, using Maya’s `usdExport` command if available.  
  - Build a USD Layers & Variant Browser to view and switch variants inside Maya.  
  - Refresh references after variant changes.

* **Consequences**:  
  - Supports USD-based workflows efficiently.  
  - Empowers artists to leverage USD variants directly in Maya.

---
