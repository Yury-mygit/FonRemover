# FonRemover

Remove image backgrounds — turn the background transparent and save a PNG —
using the local [`rembg`](https://github.com/danielgatis/rembg) engine
(U2-Net, ONNX). Runs offline after the model is downloaded on first use.

## Install

```sh
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell:  .venv\Scripts\Activate.ps1
pip install -e .
```

This registers the `fonremover` command.

## Usage

Single image (writes `photo_nobg.png` next to the input):

```sh
fonremover photo.jpg
```

Explicit output:

```sh
fonremover photo.jpg -o result.png
```

Batch — process every image in a folder (output goes to `<folder>/nobg/` by
default, or pass `-o <dir>`):

```sh
fonremover ./photos -o ./photos_nobg
```

Pick a different rembg model (e.g. `u2netp`, `isnet-general-use`,
`u2net_human_seg`):

```sh
fonremover photo.jpg --model isnet-general-use
```

Supported inputs: PNG, JPG/JPEG, WEBP, BMP, TIFF. Output is always PNG.

## Project docs / methodology

This repo follows the [ai-agent-playbook](https://github.com/Yury-mygit/ai-agent-playbook)
regulation. See `CLAUDE.md` (project handbook), `notes/ai_agent_playbook.md`
(vendored playbook), and `ideas/` (the work cards).
