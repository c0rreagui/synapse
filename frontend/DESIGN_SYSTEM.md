# Synapse Design System (Neo-Glass)

**Status**: Active
**Version**: 1.0 (Neo-Glass)

This document serves as the static reference for the Synapse Design System. For interactive examples and component usage, please refer to **Storybook** (`npm run storybook`).

---

## 🎨 Color Palette

The color system is built around a "Neo-Glass" aesthetic: deep voids, neural layers, and neon accents.

### Core Architecture

| Token | Value | Description |
| :--- | :--- | :--- |
| **Deep Void** | `#05040a` | Main background. The deepest layer of the interface. |
| **Neural Layer** | `#0f0a15` | Surface color for cards and panels. Slightly lighter than void. |
| **Glass Module** | `rgba(13, 17, 23, 0.7)` | Translucent layer for overlapping elements. |
| **Border** | `rgba(139, 92, 246, 0.2)` | Subtle purple boundary for components. |

### Neon Accents

| Token | Value | Description |
| :--- | :--- | :--- |
| **Primary (Violet)** | `#8b5cf6` | Main brand color. Used for actions, focus, and emphasis. |
| **Secondary (Magenta)** | `#d946ef` | Secondary accent. Used for creative flows or alternative states. |
| **Cyan (Info)** | `#06b6d4` | Information and data streams. |

### Semantic Signals

| Role | Color | Hex |
| :--- | :--- | :--- |
| **Success** | Emerald | `#10b981` |
| **Error** | Rose | `#fb7185` |
| **Warning** | Amber | `#f59e0b` |
| **Muted** | Violet Gray | `#a78bfa` |
| **Text** | Light Violet | `#e9d5ff` |

---

## 🌈 Gradients

Gradients are used to create depth and "aliveness".

- **Brand Gradient**: `linear-gradient(135deg, #d946ef 0%, #8b5cf6 50%, #6366f1 100%)`
  *(Magenta -> Violet -> Indigo)*
- **Glass Gradient**: `linear-gradient(135deg, rgba(15, 10, 21, 0.9) 0%, rgba(5, 4, 10, 0.95) 100%)`
- **Card Gradient**: `linear-gradient(180deg, #151020 0%, #0f0a15 100%)`

---

## 🔡 Typography

We use a pairing of **Inter** for UI clarity and **JetBrains Mono** for code and data density.

### Font Families

- **Primary (Sans)**: `Inter`, system-ui, sans-serif
- **Code (Mono)**: `JetBrains Mono`, Consolas, monospace

### Typographic Scale

| Class | Usage |
| :--- | :--- |
| `text-4xl` **Black** | Hero Headers, Marketing stats. |
| `text-3xl` **Bold** | Page Titles, Major Section Headers. |
| `text-2xl` **SemiBold** | Card Titles, Modal Headers. |
| `text-xl` **Medium** | Sub-sections, Feature names. |
| `text-base` **Regular** | Body text, standard descriptions. |
| `text-sm` **Light** | Captions, Metadata, Help text. |

---

## ✨ Visual Effects

### Glass Panel (`.glass-panel`)

- **Background**: `rgba(13, 17, 23, 0.7)`
- **Blur**: `backdrop-blur-xl` or `2xl`
- **Border**: `1px solid rgba(139, 92, 246, 0.2)`

### Neon Glow

- **Shadow**: `0 0 25px rgba(139, 92, 246, 0.2)`
- **Text Shadow**: `0 0 10px rgba(139, 92, 246, 0.6)`

### Squircle

- **Border Radius**: `32px` (Tailwind class: `rounded-neo`)
