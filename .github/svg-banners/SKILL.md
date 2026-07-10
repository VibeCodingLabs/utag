---
name: "svg-banner-generator"
description: "Generates animated SVG banners and spinners using a cobra-cli driven toolset with customizable viper flags."
license: "MIT"
compatibility: "Requires go >= 1.20, cobra-cli v1.3.0+, viper v1.20+"
metadata:
  author: "Palette"
  version: "1.0.0"
allowed-tools: "run_in_bash_session list_files read_file"
---

# 🎨 SVG Banner & Spinner Generator

This skill provides instructions for generating customizable animated SVG assets (spinners and banners) using a Go-based CLI tool powered by [Cobra](https://github.com/spf13/cobra) and [Viper](https://github.com/spf13/viper).

## 🗣️ Natural Language Invocation Phrases
You can invoke this skill by recognizing these intents:
- "Generate an SVG spinner with..."
- "Create a new loading animation..."
- "Use cobra-cli to make an svg generator tool..."
- "Build an animated SVG using the blue palette..."
- "I need a custom 180-rotate spinner..."

## 🛠️ Cobra & Viper Toolset Generation Best Practices

When instructed to create the generator tool, strictly follow these practices:
1. **Initialize the module**: Run `go mod init <module_name>`.
2. **Scaffold with cobra-cli**: Run `cobra-cli init --viper --license MIT`.
3. **Use Isolated Viper Instances**: Do not use the global `viper.Get()` singleton. Instantiate new instances (`v := viper.New()`) to avoid state collision and improve testability.
4. **Bind PFlags**:
   ```go
   cmd.Flags().String("palette", "lightblue", "Color palette for the SVG")
   v.BindPFlag("palette", cmd.Flags().Lookup("palette"))
   ```

## ⚙️ Supported Viper Flags

All generated spinner commands MUST support the following Viper-bound flags:
- `--size`: Pixel dimension of the SVG (e.g., `--size 24px`, `--size 64px`). Default: `24px`.
- `--palette`: Color scheme (e.g., `--palette lightblue`, `--palette neon-pink`, `--palette dark-mode`). Default: `black`.
- `--speed`: Animation duration (e.g., `--speed 1.5s`, `--speed fast`). Default: `1s`.
- `--rotate`: Initial rotation or animation spin degrees (e.g., `--rotate 180`, `--rotate 270`). Default: `0`.

## 📦 Progressive Disclosure & Lazy Loading

If the user requests specific SVG path data for complex spinners (like `gooey-balls-1` or `blocks-shuffle-3`), **do not hallucinate the paths**. You must lazy-load the reference data.

**Instruction:** When you need the raw path definitions for the 46 variations, use your tool to read the external reference file:
`read_file(".github/svg-banners/references/spinner_paths.md")` *(Note: create this file if it does not exist before generating the Go code)*.

## 🚀 Subcommands for Generative Output

The Cobra application should register a separate subcommand for each variation.
Example CLI usage:
```bash
go run main.go 12-dots-scale-rotate --size 24px --palette lightblue --rotate 180 --speed 1.2s
go run main.go pulse-multiple --size 48px --palette neon-green
```

### Supported SVG Spinner Commands:
`12-dots-scale-rotate`, `180-ring`, `180-ring-with-bg`, `270-ring`, `270-ring-with-bg`, `3-dots-bounce`, `3-dots-fade`, `3-dots-move`, `3-dots-rotate`, `3-dots-scale`, `3-dots-scale-middle`, `6-dots-rotate`, `6-dots-scale`, `6-dots-scale-middle`, `8-dots-rotate`, `90-ring`, `90-ring-with-bg`, `bars-fade`, `bars-rotate-fade`, `bars-scale`, `bars-scale-fade`, `bars-scale-middle`, `blocks-scale`, `blocks-shuffle-2`, `blocks-shuffle-3`, `blocks-wave`, `bouncing-ball`, `clock`, `dot-revolve`, `eclipse`, `eclipse-half`, `gooey-balls-1`, `gooey-balls-2`, `pulse`, `pulse-2`, `pulse-3`, `pulse-multiple`, `pulse-ring`, `pulse-rings-2`, `pulse-rings-3`, `pulse-rings-multiple`, `ring-resize`, `tadpole`, `wifi`, `wifi-fade`, `wind-toy`.
