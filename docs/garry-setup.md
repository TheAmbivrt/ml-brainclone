# Garry Setup — Spatial Brain (Image-to-3D)

Garry is Larry's spatial agent. Converts images to 3D meshes (GLB) via Trellis 2, with automatic background removal (rembg) and Blender import.

---

## Quick Start

```bash
# Convert image to 3D mesh
python 03-projects/ml-brainclone/agents/garry_service.py generate "path/to/image.png"

# With custom output directory
python 03-projects/ml-brainclone/agents/garry_service.py generate "image.png" --output "path/to/output/"

# Check status
python 03-projects/ml-brainclone/agents/garry_service.py status
```

---

## Architecture

```
User → Larry → garry_service.py (CLI)
  → rembg removes background (local, GPU-accelerated)
  → Trellis 2 generates 3D mesh (HuggingFace/fal.ai API)
  → GLB output saved to {{GARRY_PATH}}/
  → Optional: Blender import via Blender MCP
  → Bus event: garry-mesh-generated
  → Metadata logged (source image, params, output path)
```

---

## File Structure

```
{{GARRY_PATH}}/
├── meshes/                 ← Generated 3D meshes (GLB/FBX)
│   ├── characters/         ← Character meshes
│   ├── environments/       ← Scene/environment meshes
│   ├── props/              ← Object meshes
│   └── raw/                ← Unsorted output
├── textures/               ← Extracted/generated textures
├── blender/                ← Blender project files (.blend)
└── source/                 ← Source images used for generation
```

---

## Prerequisites

| Component | Required? | Notes |
|-----------|-----------|-------|
| **Python 3.10+** | Yes | Runtime |
| **rembg** | Yes | Background removal (`pip install rembg[gpu]` for CUDA) |
| **Trellis 2** | Yes | Image-to-3D model (via HuggingFace or fal.ai API) |
| **Blender 4.0+** | Optional | For import, rigging, and scene assembly |
| **NVIDIA GPU (CUDA)** | Recommended | Accelerates rembg and local Trellis inference |
| **fal.ai API key** | Optional | For cloud-based Trellis inference (alternative to local) |

### Install rembg

```bash
# GPU-accelerated (recommended)
pip install rembg[gpu]

# CPU-only fallback
pip install rembg
```

### Trellis 2 Setup

Trellis 2 can run locally (requires significant VRAM) or via fal.ai API:

```bash
# Option 1: fal.ai (cloud, easier setup)
pip install fal-client
# Set FAL_KEY in environment or config

# Option 2: Local (requires ~8GB VRAM)
# Follow Trellis 2 repo instructions: https://github.com/microsoft/TRELLIS
```

### Blender MCP (Optional)

For programmatic Blender import, install the Blender MCP server:

```bash
pip install blender-mcp
# Configure in .mcp.json
```

---

## Pipeline

### 1. Background Removal

Every input image passes through rembg first. This isolates the subject for cleaner 3D reconstruction.

```
Input image → rembg → Clean subject (transparent background) → Trellis 2
```

### 2. Mesh Generation

Trellis 2 converts the cleaned image to a 3D mesh in GLB format.

### 3. Post-Processing

- GLB saved to `{{GARRY_PATH}}/meshes/<category>/`
- Source image copied to `{{GARRY_PATH}}/source/`
- Metadata logged: source path, generation params, output path, timestamp
- Bus event emitted: `garry-mesh-generated`

### 4. Blender Import (Optional)

When a mesh needs rigging, texturing, or scene assembly, Garry imports it into Blender via MCP.

---

## Barry → Garry Pipeline

Barry-generated images can flow directly into Garry for 3D conversion:

```
Barry generates image → Image saved to {{ASSETS_PATH}}/
  → Larry invokes Garry with image path
  → Garry produces GLB mesh
  → Mesh available for Blender scene assembly
```

---

## Bus Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `garry-mesh-request` | In | `{image_path, category, params}` |
| `garry-mesh-generated` | Out | `{mesh_path, source_image, format, vertices}` |
| `garry-error` | Out | `{error, image_path}` |

---

## Configuration

`agents/garry-config.json`:

```json
{
  "garry_root": "{{GARRY_PATH}}",
  "trellis_backend": "fal",
  "rembg_model": "u2net",
  "default_format": "glb",
  "blender_mcp": false,
  "log_file": "agents/logs/garry.log"
}
```

---

## Placeholders

| Placeholder | Replace with |
|-------------|--------------|
| `{{GARRY_PATH}}` | Path to your 3D assets directory (e.g., `D:\04-Garry`) |
| `{{ASSETS_PATH}}` | Path to your Barry image assets (for pipeline integration) |
