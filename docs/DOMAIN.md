# Domain

## Core domain concepts

### Template-bound generation

The system generates slides and decks inside the boundaries of a real PowerPoint template rather than recreating its design heuristically.

### Manifest package

A manifest package is the extracted representation of a source template, including layout contracts, assets, fingerprints, compatibility information, and layered human annotations.

### Layout contract

A layout contract describes an approved slide layout, its placeholders, geometry, allowed content types, and validation rules.

### Protected static elements

Protected static elements are template-owned visual objects that must not move or change unintentionally during generation.

### Fidelity

Fidelity means preserving structural and visual constraints from the source template. In this project, fidelity is strongest where preserved source assets can be reused directly.

### Agent-first CLI contract

The CLI itself is part of the product domain. Commands, errors, exit codes, and response shapes are treated as stable interfaces for automation rather than incidental terminal output.

## Domain boundaries

This project is not a generic slide editor. It is a template compiler, layout contract inspector, deck composer, validator, and diff tool for enterprise PowerPoint workflows.
