# Simulador Econômico 3D

Simulador econômico com visualização 3D Low-Poly desenvolvido para a disciplina de **Computação Gráfica e Realidade Virtual**.

## Descrição

Aplicação interativa que combina mecânicas de simulação econômica com renderização 3D em tempo real utilizando OpenGL. O jogador gerencia uma empresa, construindo edificações, comprando/vendendo recursos e acompanhando a evolução visual da sua cidade industrial.

## Requisitos

- Python 3.8+
- PySide6
- PyOpenGL
- NumPy

## Instalação

```bash
pip install PySide6 PyOpenGL numpy
```

## Execução

```bash
python simulador3d.py
```

## Conceitos de CG Aplicados

- **Primitivas 3D**: Boxes, cilindros e prismas triangulares
- **Transformações**: Translação, rotação e escala hierárquicas
- **Iluminação**: Modelo Phong com luz direcional
- **Animações**: Procedurais em tempo real (fumaça, água, rotações)
- **Materiais**: Cores e propriedades de reflexão

## Estrutura do Projeto

```
simulador3d.py
├── Modelos de Dados (Recurso, Construcao, Evento, Conquista)
├── Lógica de Negócio (Empresa)
├── Renderização 3D (GLWidget, funções draw_*)
└── Interface Gráfica (MainWindow)
```

## Controles

| Ação | Controle |
|------|----------|
| Rotacionar câmera | Arrastar com mouse |
| Zoom | Scroll do mouse |

## Funcionalidades

- 8 tipos de construções com modelos 3D únicos
- Sistema de upgrades (5 níveis por construção)
- Mercado dinâmico com volatilidade de preços
- Eventos aleatórios e sistema de conquistas
- Save/Load em formato JSON

## Licença

Projeto acadêmico - Uso educacional.
