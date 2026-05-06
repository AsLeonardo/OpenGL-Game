# 3D Economic Simulator

**Authors**
- Andrey Justen Júnior
- Bárbara Prim de Souza
- Mateus Nunes Lehmkuhl
- Leonardo Alves Silva

An economic simulator with low-poly 3D visualization, developed for the **Computer Graphics and Virtual Reality** course.

## Description

An interactive application that combines economic simulation mechanics with real-time 3D rendering using OpenGL. The player manages a company by constructing buildings, buying and selling resources, and watching their industrial city evolve visually as the business grows.

<img width="1080" alt="Image" src="https://github.com/user-attachments/assets/ee47a3f5-a26c-40e1-bdf6-6102620a8797" />

## Requirements

- Python 3.8+
- PySide6
- PyOpenGL
- NumPy

## Installation

```bash
pip install PySide6 PyOpenGL numpy
```

## Running

```bash
python 3dsimulator.py
```

## Computer Graphics Concepts Applied

- **3D Primitives:** boxes, cylinders, and triangular prisms
- **Transformations:** hierarchical translation, rotation, and scaling
- **Lighting:** Phong shading model with directional light
- **Animations:** real-time procedural effects (smoke, water, rotations)
- **Materials:** colors and reflection properties

## Project Structure

```
3dsimulator.py
├── Data Models (Resource, Building, Event, Achievement)
├── Business Logic (Company)
├── 3D Rendering (GLWidget, draw functions)
└── Graphical Interface (MainWindow)
```

## Controls

| Action          | Control            |
|-----------------|--------------------|
| Rotate camera   | Click & drag mouse |
| Zoom in / out   | Mouse scroll       |
| Movement        | WASD Keys          |

## Features

- 8 building types, each with a unique 3D model
- Upgrade system (5 levels per building)
- Dynamic market with price volatility
- Random events and achievement system
- Save / Load support in JSON format
