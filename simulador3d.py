# simulador3d_enhanced.py
# Enhanced 3D Economic Simulator with Low-Poly Graphics
# Features: Better visuals, more buildings, price charts, events, achievements, save/load
# Requires: PySide6, PyOpenGL, numpy

import sys
import math
import random
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque
from datetime import datetime

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QSurfaceFormat, QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSpinBox, QFormLayout, QComboBox, QMessageBox,
    QProgressBar, QTabWidget, QGroupBox, QGridLayout, QScrollArea, QFrame,
    QFileDialog, QToolTip, QSplitter
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QTimer, Signal

from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# STYLES - Modern Dark Theme
# ═══════════════════════════════════════════════════════════════════════════════

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #eaeaea;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}
QLabel {
    color: #eaeaea;
}
QLabel#title {
    font-size: 18px;
    font-weight: bold;
    color: #4fc3f7;
    padding: 10px;
}
QLabel#sectionTitle {
    font-size: 14px;
    font-weight: bold;
    color: #81d4fa;
    padding: 5px 0;
}
QPushButton {
    background-color: #0f3460;
    color: #eaeaea;
    border: 1px solid #16213e;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1a4a7a;
    border-color: #4fc3f7;
}
QPushButton:pressed {
    background-color: #0a2540;
}
QPushButton:disabled {
    background-color: #2a2a3e;
    color: #666;
}
QPushButton#actionBtn {
    background-color: #00897b;
}
QPushButton#actionBtn:hover {
    background-color: #00a08a;
}
QPushButton#dangerBtn {
    background-color: #c62828;
}
QPushButton#dangerBtn:hover {
    background-color: #e53935;
}
QPushButton#successBtn {
    background-color: #2e7d32;
}
QPushButton#successBtn:hover {
    background-color: #43a047;
}
QListWidget {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 6px;
    padding: 4px;
}
QListWidget::item {
    padding: 6px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #0f3460;
    color: #4fc3f7;
}
QListWidget::item:hover {
    background-color: #1a3a5c;
}
QComboBox {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 6px;
    padding: 6px 12px;
    color: #eaeaea;
}
QComboBox:hover {
    border-color: #4fc3f7;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    border: 1px solid #0f3460;
    selection-background-color: #0f3460;
}
QSpinBox {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 6px;
    padding: 6px;
    color: #eaeaea;
}
QSpinBox:hover {
    border-color: #4fc3f7;
}
QGroupBox {
    border: 1px solid #0f3460;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
    color: #81d4fa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QProgressBar {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 6px;
    height: 20px;
    text-align: center;
    color: #eaeaea;
}
QProgressBar::chunk {
    background-color: #00897b;
    border-radius: 5px;
}
QTabWidget::pane {
    border: 1px solid #0f3460;
    border-radius: 6px;
    background-color: #1a1a2e;
}
QTabBar::tab {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #0f3460;
    color: #4fc3f7;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QFrame#card {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 10px;
}
QToolTip {
    background-color: #0f3460;
    color: #eaeaea;
    border: 1px solid #4fc3f7;
    border-radius: 4px;
    padding: 6px;
}
"""

# ═══════════════════════════════════════════════════════════════════════════════
# GAME DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Recurso:
    nome: str
    quantidade: int
    preco: float
    volatilidade: float
    simbolo: str
    cor: tuple = (1.0, 1.0, 1.0)
    preco_historico: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.preco_historico:
            self.preco_historico = [self.preco]

@dataclass
class ConstrucaoModelo:
    id: str
    nome: str
    custo: float
    producao_recurso: Optional[str]
    taxa_producao: int
    manutencao: float
    simbolo: str
    pesquisa: int = 0
    nivel_max: int = 5
    descricao: str = ""
    cor_principal: tuple = (0.5, 0.5, 0.5)

@dataclass 
class Construcao:
    modelo: ConstrucaoModelo
    nivel: int = 1
    built_at: int = 0
    
    @property
    def manutencao_atual(self):
        return self.modelo.manutencao * (1 + (self.nivel - 1) * 0.3)
    
    @property
    def producao_atual(self):
        return int(self.modelo.taxa_producao * (1 + (self.nivel - 1) * 0.5))
    
    @property
    def custo_upgrade(self):
        return int(self.modelo.custo * 0.5 * self.nivel)

@dataclass
class Evento:
    titulo: str
    descricao: str
    tipo: str  # 'bonus', 'penalty', 'neutral', 'special'
    icone: str

@dataclass
class Conquista:
    id: str
    nome: str
    descricao: str
    icone: str
    condicao: str
    desbloqueada: bool = False
    turno_desbloqueio: int = 0

# ═══════════════════════════════════════════════════════════════════════════════
# EMPRESA (GAME STATE)
# ═══════════════════════════════════════════════════════════════════════════════

class Empresa:
    def __init__(self):
        self.capital: float = 15000.0
        self.turno: int = 1
        self.pontos_pesquisa: int = 0
        self.recursos: Dict[str, Recurso] = {}
        self.construcoes: List[Construcao] = []
        self.modelos_construcao: Dict[str, ConstrucaoModelo] = {}
        self.eventos_log: deque = deque(maxlen=20)
        self.conquistas: Dict[str, Conquista] = {}
        self.estatisticas = {
            'total_ganho': 0.0,
            'total_gasto': 0.0,
            'turnos_jogados': 0,
            'construcoes_feitas': 0,
            'upgrades_feitos': 0,
            'recursos_vendidos': 0,
            'eventos_ocorridos': 0,
            'max_capital': 15000.0
        }
        self._init_recursos()
        self._init_modelos()
        self._init_conquistas()
    
    def _init_recursos(self):
        recursos_data = [
            ('madeira', 'Madeira', 100, 5.00, 0.15, '🌲', (0.4, 0.26, 0.13)),
            ('metal', 'Metal', 50, 20.00, 0.20, '🔩', (0.6, 0.6, 0.65)),
            ('cafe', 'Café', 20, 50.00, 0.10, '☕', (0.4, 0.26, 0.13)),
            ('energia', 'Energia', 200, 2.50, 0.05, '⚡', (1.0, 0.9, 0.2)),
            ('petroleo', 'Petróleo', 10, 85.00, 0.25, '🛢️', (0.15, 0.15, 0.15)),
            ('ouro', 'Ouro', 5, 150.00, 0.35, '🪙', (1.0, 0.84, 0.0)),
        ]
        for id_, nome, qtd, preco, vol, simb, cor in recursos_data:
            self.recursos[id_] = Recurso(nome, qtd, preco, vol, simb, cor)
    
    def _init_modelos(self):
        modelos = [
            ConstrucaoModelo('madeira', 'Serraria', 1500, 'madeira', 50, 30, '🏭',
                           descricao='Produz madeira de reflorestamento', cor_principal=(0.6, 0.45, 0.3)),
            ConstrucaoModelo('metal', 'Mineradora', 3000, 'metal', 25, 75, '⛏️',
                           descricao='Extrai metais preciosos', cor_principal=(0.4, 0.4, 0.45)),
            ConstrucaoModelo('energia', 'Hidrelétrica', 4000, 'energia', 100, 120, '💡',
                           descricao='Gera energia limpa', cor_principal=(0.3, 0.5, 0.7)),
            ConstrucaoModelo('cafe', 'Cafezal', 5000, 'cafe', 10, 100, '🌿',
                           descricao='Plantação de café premium', cor_principal=(0.2, 0.5, 0.2)),
            ConstrucaoModelo('petroleo', 'Refinaria', 8000, 'petroleo', 8, 200, '🏗️',
                           descricao='Refina petróleo bruto', cor_principal=(0.3, 0.3, 0.35)),
            ConstrucaoModelo('ouro', 'Mina de Ouro', 12000, 'ouro', 3, 350, '💎',
                           descricao='Extrai ouro e gemas', cor_principal=(0.8, 0.7, 0.2)),
            ConstrucaoModelo('pesquisa', 'Centro de P&D', 7000, None, 0, 200, '🔬',
                           pesquisa=10, descricao='Gera pontos de pesquisa', cor_principal=(0.35, 0.4, 0.9)),
            ConstrucaoModelo('banco', 'Banco', 10000, None, 0, 150, '🏦',
                           descricao='Gera 2% de juros por turno', cor_principal=(0.5, 0.5, 0.55)),
        ]
        self.modelos_construcao = {m.id: m for m in modelos}
    
    def _init_conquistas(self):
        conquistas = [
            Conquista('primeiro_turno', 'Iniciante', 'Complete o primeiro turno', '🎯', 'turno >= 2'),
            Conquista('capital_50k', 'Investidor', 'Alcance R$ 50.000', '💰', 'capital >= 50000'),
            Conquista('capital_100k', 'Magnata', 'Alcance R$ 100.000', '💎', 'capital >= 100000'),
            Conquista('capital_500k', 'Bilionário', 'Alcance R$ 500.000', '👑', 'capital >= 500000'),
            Conquista('5_construcoes', 'Construtor', 'Construa 5 edificações', '🏗️', 'construcoes >= 5'),
            Conquista('10_construcoes', 'Desenvolvedor', 'Construa 10 edificações', '🏙️', 'construcoes >= 10'),
            Conquista('pesquisa_100', 'Cientista', 'Alcance 100 pontos de pesquisa', '🔬', 'pesquisa >= 100'),
            Conquista('turno_50', 'Veterano', 'Sobreviva 50 turnos', '⭐', 'turno >= 50'),
            Conquista('upgrade_max', 'Perfeccionista', 'Faça upgrade de uma construção ao nível máximo', '🏆', 'max_nivel >= 5'),
            Conquista('diversificado', 'Diversificado', 'Tenha pelo menos 4 tipos de construção', '🌈', 'tipos_construcao >= 4'),
        ]
        self.conquistas = {c.id: c for c in conquistas}
    
    def verificar_conquistas(self):
        novas = []
        
        stats = {
            'turno': self.turno,
            'capital': self.capital,
            'construcoes': len(self.construcoes),
            'pesquisa': self.pontos_pesquisa,
            'max_nivel': max([c.nivel for c in self.construcoes], default=0),
            'tipos_construcao': len(set(c.modelo.id for c in self.construcoes)),
        }
        
        for c in self.conquistas.values():
            if c.desbloqueada:
                continue
            try:
                if eval(c.condicao, {"__builtins__": {}}, stats):
                    c.desbloqueada = True
                    c.turno_desbloqueio = self.turno
                    novas.append(c)
            except:
                pass
        
        return novas
    
    def custo_manutencao_total(self):
        return sum(c.manutencao_atual for c in self.construcoes)
    
    def avancar_turno(self):
        eventos = []
        
        # Manutenção
        manut = self.custo_manutencao_total()
        self.capital -= manut
        self.estatisticas['total_gasto'] += manut
        
        # Produção
        for c in self.construcoes:
            modelo = c.modelo
            if modelo.producao_recurso:
                prod = c.producao_atual
                self.recursos[modelo.producao_recurso].quantidade += prod
            if modelo.pesquisa:
                bonus = int(modelo.pesquisa * (1 + (c.nivel - 1) * 0.3))
                self.pontos_pesquisa += bonus
            
            # Banco gera juros
            if modelo.id == 'banco':
                juros = self.capital * 0.02 * c.nivel
                self.capital += juros
                self.estatisticas['total_ganho'] += juros
        
        # Volatilidade de preços
        for r in self.recursos.values():
            var = random.uniform(-r.volatilidade, r.volatilidade)
            r.preco = max(0.1, round(r.preco * (1 + var), 2))
            r.preco_historico.append(r.preco)
            if len(r.preco_historico) > 50:
                r.preco_historico.pop(0)
        
        # Eventos aleatórios (30% chance)
        if random.random() < 0.30:
            evento = self._gerar_evento()
            eventos.append(evento)
            self.eventos_log.appendleft(evento)
            self.estatisticas['eventos_ocorridos'] += 1
        
        self.turno += 1
        self.estatisticas['turnos_jogados'] += 1
        self.estatisticas['max_capital'] = max(self.estatisticas['max_capital'], self.capital)
        
        # Verificar conquistas
        novas_conquistas = self.verificar_conquistas()
        
        return eventos, novas_conquistas
    
    def _gerar_evento(self) -> Evento:
        eventos_possiveis = [
            # Bônus
            ('bonus', '📈 Boom de Mercado!', 'O preço de {recurso} subiu 60%!', 
             lambda r: setattr(r, 'preco', round(r.preco * 1.6, 2))),
            ('bonus', '🎁 Doação Recebida', 'Você recebeu R$ 2.000 de um investidor!',
             lambda _: setattr(self, 'capital', self.capital + 2000)),
            ('bonus', '⚡ Eficiência Energética', 'Sua produção de energia dobrou este turno!',
             lambda _: None),
            
            # Penalidades  
            ('penalty', '📉 Crise no Setor', 'O preço de {recurso} caiu 40%!',
             lambda r: setattr(r, 'preco', max(0.5, round(r.preco * 0.6, 2)))),
            ('penalty', '🔧 Manutenção Extra', 'Reparos emergenciais custaram R$ 1.000!',
             lambda _: setattr(self, 'capital', self.capital - 1000)),
            ('penalty', '🌧️ Clima Adverso', 'A produção de café foi afetada!',
             lambda _: None),
            
            # Neutros
            ('neutral', '📊 Mercado Estável', 'Não houve grandes mudanças hoje.',
             lambda _: None),
            ('neutral', '🔄 Flutuação Normal', 'Os mercados operaram normalmente.',
             lambda _: None),
        ]
        
        tipo, titulo, desc, efeito = random.choice(eventos_possiveis)
        
        recurso_alvo = random.choice(list(self.recursos.keys()))
        recurso = self.recursos[recurso_alvo]
        
        if '{recurso}' in desc:
            desc = desc.format(recurso=recurso.nome)
            efeito(recurso)
        else:
            efeito(recurso)
        
        icone = {'bonus': '✅', 'penalty': '⚠️', 'neutral': 'ℹ️', 'special': '⭐'}[tipo]
        
        return Evento(titulo, desc, tipo, icone)
    
    def comprar_recurso(self, chave: str, quantidade: int):
        r = self.recursos[chave]
        custo = quantidade * r.preco
        if custo > self.capital:
            raise ValueError("Capital insuficiente")
        self.capital -= custo
        r.quantidade += quantidade
        self.estatisticas['total_gasto'] += custo
    
    def vender_recurso(self, chave: str, quantidade: int):
        r = self.recursos[chave]
        if quantidade > r.quantidade:
            raise ValueError("Quantidade insuficiente")
        ganho = quantidade * r.preco
        self.capital += ganho
        r.quantidade -= quantidade
        self.estatisticas['total_ganho'] += ganho
        self.estatisticas['recursos_vendidos'] += quantidade
    
    def construir(self, modelo_id: str):
        modelo = self.modelos_construcao[modelo_id]
        if self.capital < modelo.custo:
            raise ValueError("Capital insuficiente")
        self.capital -= modelo.custo
        self.estatisticas['total_gasto'] += modelo.custo
        self.estatisticas['construcoes_feitas'] += 1
        self.construcoes.append(Construcao(modelo=modelo, nivel=1, built_at=self.turno))
    
    def upgrade_construcao(self, index: int):
        if index < 0 or index >= len(self.construcoes):
            raise ValueError("Construção inválida")
        
        c = self.construcoes[index]
        if c.nivel >= c.modelo.nivel_max:
            raise ValueError("Nível máximo atingido")
        
        custo = c.custo_upgrade
        if self.capital < custo:
            raise ValueError("Capital insuficiente")
        
        self.capital -= custo
        c.nivel += 1
        self.estatisticas['total_gasto'] += custo
        self.estatisticas['upgrades_feitos'] += 1
    
    def demolir_construcao(self, index: int):
        if index < 0 or index >= len(self.construcoes):
            raise ValueError("Construção inválida")
        
        c = self.construcoes[index]
        reembolso = c.modelo.custo * 0.3  # 30% de reembolso
        self.capital += reembolso
        self.estatisticas['total_ganho'] += reembolso
        self.construcoes.pop(index)
    
    def to_dict(self) -> dict:
        return {
            'capital': self.capital,
            'turno': self.turno,
            'pontos_pesquisa': self.pontos_pesquisa,
            'recursos': {k: {'quantidade': v.quantidade, 'preco': v.preco, 
                            'preco_historico': v.preco_historico} 
                        for k, v in self.recursos.items()},
            'construcoes': [{'modelo_id': c.modelo.id, 'nivel': c.nivel, 'built_at': c.built_at} 
                           for c in self.construcoes],
            'conquistas': {k: {'desbloqueada': v.desbloqueada, 'turno': v.turno_desbloqueio}
                          for k, v in self.conquistas.items()},
            'estatisticas': self.estatisticas,
        }
    
    def from_dict(self, data: dict):
        self.capital = data['capital']
        self.turno = data['turno']
        self.pontos_pesquisa = data['pontos_pesquisa']
        
        for k, v in data['recursos'].items():
            if k in self.recursos:
                self.recursos[k].quantidade = v['quantidade']
                self.recursos[k].preco = v['preco']
                self.recursos[k].preco_historico = v.get('preco_historico', [v['preco']])
        
        self.construcoes = []
        for c_data in data['construcoes']:
            modelo = self.modelos_construcao[c_data['modelo_id']]
            self.construcoes.append(Construcao(
                modelo=modelo, nivel=c_data['nivel'], built_at=c_data['built_at']
            ))
        
        for k, v in data.get('conquistas', {}).items():
            if k in self.conquistas:
                self.conquistas[k].desbloqueada = v['desbloqueada']
                self.conquistas[k].turno_desbloqueio = v['turno']
        
        self.estatisticas = data.get('estatisticas', self.estatisticas)

# ═══════════════════════════════════════════════════════════════════════════════
# OPENGL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def draw_box(w, h, d):
    hw, hh, hd = w/2.0, h/2.0, d/2.0
    glBegin(GL_QUADS)
    glNormal3f(0,0,1)
    glVertex3f(-hw,-hh, hd); glVertex3f(hw,-hh, hd); glVertex3f(hw,hh, hd); glVertex3f(-hw,hh, hd)
    glNormal3f(0,0,-1)
    glVertex3f(-hw,-hh,-hd); glVertex3f(-hw,hh,-hd); glVertex3f(hw,hh,-hd); glVertex3f(hw,-hh,-hd)
    glNormal3f(-1,0,0)
    glVertex3f(-hw,-hh,-hd); glVertex3f(-hw,-hh, hd); glVertex3f(-hw,hh, hd); glVertex3f(-hw,hh,-hd)
    glNormal3f(1,0,0)
    glVertex3f(hw,-hh,-hd); glVertex3f(hw,hh,-hd); glVertex3f(hw,hh, hd); glVertex3f(hw,-hh, hd)
    glNormal3f(0,1,0)
    glVertex3f(-hw,hh,-hd); glVertex3f(-hw,hh, hd); glVertex3f(hw,hh, hd); glVertex3f(hw,hh,-hd)
    glNormal3f(0,-1,0)
    glVertex3f(-hw,-hh,-hd); glVertex3f(hw,-hh,-hd); glVertex3f(hw,-hh, hd); glVertex3f(-hw,-hh, hd)
    glEnd()

def draw_prism_triangle(base, height, depth):
    glBegin(GL_TRIANGLES)
    glNormal3f(0,0,1)
    glVertex3f(-base/2, -height/2, depth/2)
    glVertex3f(base/2, -height/2, depth/2)
    glVertex3f(0, height/2, depth/2)
    glNormal3f(0,0,-1)
    glVertex3f(-base/2, -height/2, -depth/2)
    glVertex3f(0, height/2, -depth/2)
    glVertex3f(base/2, -height/2, -depth/2)
    glEnd()
    glBegin(GL_QUADS)
    glNormal3f(-1,0,0)
    glVertex3f(-base/2,-height/2, depth/2)
    glVertex3f(-base/2,-height/2,-depth/2)
    glVertex3f(0,height/2,-depth/2)
    glVertex3f(0,height/2, depth/2)
    glNormal3f(1,0,0)
    glVertex3f(base/2,-height/2, depth/2)
    glVertex3f(0,height/2, depth/2)
    glVertex3f(0,height/2,-depth/2)
    glVertex3f(base/2,-height/2,-depth/2)
    glNormal3f(0,-1,0)
    glVertex3f(-base/2,-height/2, depth/2)
    glVertex3f(base/2,-height/2, depth/2)
    glVertex3f(base/2,-height/2,-depth/2)
    glVertex3f(-base/2,-height/2,-depth/2)
    glEnd()

def draw_cylinder(radius, height, segments=12):
    glBegin(GL_QUAD_STRIP)
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glNormal3f(math.cos(angle), 0, math.sin(angle))
        glVertex3f(x, -height/2, z)
        glVertex3f(x, height/2, z)
    glEnd()
    # Top cap
    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(0, 1, 0)
    glVertex3f(0, height/2, 0)
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        glVertex3f(radius * math.cos(angle), height/2, radius * math.sin(angle))
    glEnd()
    # Bottom cap
    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(0, -1, 0)
    glVertex3f(0, -height/2, 0)
    for i in range(segments, -1, -1):
        angle = 2 * math.pi * i / segments
        glVertex3f(radius * math.cos(angle), -height/2, radius * math.sin(angle))
    glEnd()

# ═══════════════════════════════════════════════════════════════════════════════
# LOW-POLY BUILDING MODELS
# ═══════════════════════════════════════════════════════════════════════════════

def draw_factory(scale=1.0, prod_level=1.0, t=0.0, nivel=1):
    glPushMatrix()
    glScalef(scale, scale * (1 + nivel * 0.1), scale)
    
    # Main building
    glColor3f(0.6, 0.45, 0.3)
    draw_box(2.0, 1.4, 1.6)
    
    # Roof
    glTranslatef(0, 0.9, 0)
    glColor3f(0.4, 0.2, 0.15)
    draw_prism_triangle(2.4, 0.8, 1.6)
    glPopMatrix()
    
    # Chimney with smoke
    if prod_level > 0.2:
        glPushMatrix()
        glTranslatef(1.1*scale, 0.9*scale, 0)
        glColor3f(0.35, 0.35, 0.35)
        glPushMatrix()
        glScalef(scale*0.25, scale*1.2, scale*0.25)
        draw_box(1, 1, 1)
        glPopMatrix()
        
        # Smoke particles
        glDisable(GL_LIGHTING)
        for i in range(3 + nivel):
            y = 1.2*scale + (t*0.6 + i*0.8) % 1.5
            alpha = max(0.1, 1.0 - (y - 1.2*scale) / 1.5)
            glColor4f(0.2, 0.2, 0.25, alpha * 0.6)
            glPushMatrix()
            glTranslatef(math.sin(t + i) * 0.1, y, math.cos(t + i) * 0.1)
            size = 0.15*scale*(1 + i*0.3)
            glScalef(size, size, size)
            draw_box(1, 1, 1)
            glPopMatrix()
        glEnable(GL_LIGHTING)
        glPopMatrix()
    
    # Level indicator lights
    glDisable(GL_LIGHTING)
    for i in range(nivel):
        glPushMatrix()
        glTranslatef(-0.8 + i * 0.35, 0.8*scale, 0.82*scale)
        intensity = 0.5 + 0.5 * math.sin(t * 3 + i)
        glColor3f(0.2 * intensity, 0.8 * intensity, 0.2 * intensity)
        draw_box(0.15, 0.15, 0.05)
        glPopMatrix()
    glEnable(GL_LIGHTING)

def draw_mine(scale=1.0, prod_level=1.0, t=0.0, nivel=1):
    glPushMatrix()
    glScalef(scale, scale * (1 + nivel * 0.1), scale)
    
    # Main tower
    glColor3f(0.4, 0.4, 0.45)
    draw_box(1.0, 2.0 + nivel * 0.2, 1.0)
    
    # Conveyor belt
    glPushMatrix()
    glTranslatef(-0.9, -0.2, 0)
    glRotatef(-25, 0, 0, 1)
    glColor3f(0.25, 0.2, 0.18)
    draw_box(1.6, 0.18, 0.6)
    glPopMatrix()
    
    # Mining wheel
    glPushMatrix()
    glTranslatef(0, 1.2 + nivel * 0.1, 0)
    glRotatef(t * 50 * prod_level, 0, 0, 1)
    glColor3f(0.5, 0.5, 0.5)
    glRotatef(90, 1, 0, 0)
    draw_cylinder(0.4, 0.1, 8)
    glPopMatrix()
    
    glPopMatrix()
    
    # Moving cart
    glPushMatrix()
    offset = math.sin(t * 2.0) * prod_level
    glTranslatef(-0.9 + 0.5 * offset, 0.4, 0)
    glColor3f(0.6, 0.45, 0.35)
    glScalef(0.4*scale, 0.3*scale, 0.4*scale)
    draw_box(1, 1, 1)
    glPopMatrix()

def draw_hydro(scale=1.0, prod_level=1.0, t=0.0, nivel=1):
    glPushMatrix()
    glScalef(scale, scale, scale)
    
    # Dam wall
    glColor3f(0.5, 0.55, 0.6)
    draw_box(2.5, 1.0 + nivel * 0.15, 1.2)
    
    # Control tower
    glPushMatrix()
    glTranslatef(0, 0.9, 0.6)
    glColor3f(0.45, 0.5, 0.55)
    draw_box(0.6, 0.9 + nivel * 0.1, 0.6)
    glPopMatrix()
    
    # Turbine housing
    for i in range(min(nivel, 3)):
        glPushMatrix()
        glTranslatef(-0.7 + i * 0.7, -0.3, -0.7)
        glColor3f(0.35, 0.4, 0.45)
        draw_cylinder(0.25, 0.3, 8)
        glPopMatrix()
    
    glPopMatrix()
    
    # Animated water
    glPushMatrix()
    glTranslatef(0, -0.2, -0.6)
    glDisable(GL_LIGHTING)
    
    level = -0.2 + 0.1 * math.sin(t * 1.5) * prod_level
    wave_intensity = 0.05 * prod_level
    
    glColor4f(0.05, 0.4, 0.7, 0.85)
    glBegin(GL_QUADS)
    for i in range(4):
        for j in range(4):
            x1 = -1.8 + i * 0.9
            x2 = x1 + 0.9
            z1 = -1.2 + j * 0.3
            z2 = z1 + 0.3
            h1 = level + wave_intensity * math.sin(t * 2 + i + j)
            h2 = level + wave_intensity * math.sin(t * 2 + i + j + 1)
            glVertex3f(x1, h1, z1)
            glVertex3f(x2, h1, z2)
            glVertex3f(x2, h2, z2)
            glVertex3f(x1, h2, z1)
    glEnd()
    glEnable(GL_LIGHTING)
    glPopMatrix()

def draw_coffee(scale=1.0, prod_level=1.0, t=0.0, nivel=1):
    rows = 3 + nivel
    cols = 4 + nivel
    spacing = 0.7 * scale
    
    for r in range(rows):
        for c in range(cols):
            x = (c - (cols-1)/2) * spacing
            z = (r - (rows-1)/2) * spacing
            
            # Growth animation
            growth = 0.3 + 0.5 * prod_level * (0.7 + 0.3 * math.sin((r+c) * 0.5 + t * 0.5))
            
            glPushMatrix()
            glTranslatef(x, 0.1 + growth/2, z)
            
            # Bush
            green_var = 0.1 * math.sin(r + c)
            glColor3f(0.15, 0.45 + green_var, 0.15)
            glScalef(0.35*scale, growth, 0.35*scale)
            draw_box(1, 1, 1)
            glPopMatrix()
            
            # Coffee berries (when productive)
            if prod_level > 0.3 and (r + c) % 2 == 0:
                glPushMatrix()
                glTranslatef(x + 0.1, 0.15 + growth * 0.7, z + 0.1)
                glColor3f(0.6, 0.15, 0.1)
                glScalef(0.08, 0.08, 0.08)
                draw_box(1, 1, 1)
                glPopMatrix()

def draw_research(scale=1.0, prod_level=1.0, t=0.0, nivel=1):
    glPushMatrix()
    glScalef(scale, scale * (1 + nivel * 0.08), scale)
    
    # Main building (modern style)
    glColor3f(0.35, 0.4, 0.85)
    draw_box(1.6, 1.0, 1.2)
    
    # Glass panels
    glColor4f(0.4, 0.6, 0.9, 0.8)
    glPushMatrix()
    glTranslatef(0, 0, 0.61)
    draw_box(1.2, 0.6, 0.02)
    glPopMatrix()
    
    # Antenna
    glTranslatef(0, 0.8, 0)
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glScalef(0.08, 0.7 + nivel * 0.1, 0.08)
    draw_box(1, 1, 1)
    glPopMatrix()
    
    # Satellite dish
    glPushMatrix()
    glTranslatef(0.5, 0.4, 0)
    glRotatef(30, 0, 0, 1)
    glRotatef(t * 20, 0, 1, 0)
    glColor3f(0.6, 0.6, 0.65)
    glScalef(0.3, 0.15, 0.3)
    draw_box(1, 0.2, 1)
    glPopMatrix()
    
    glPopMatrix()
    
    # Blinking lights
    glDisable(GL_LIGHTING)
    for i in range(nivel + 1):
        glPushMatrix()
        glTranslatef(0.5 - i * 0.25, 0.5 * scale, 0.62 * scale)
        intensity = 0.4 + 0.6 * (math.sin(t * 3.0 + i * 1.5) * 0.5 + 0.5)
        glColor4f(1.0, 0.9, 0.2, intensity)
        draw_box(0.1, 0.1, 0.02)
        glPopMatrix()
    glEnable(GL_LIGHTING)

def draw_refinery(scale=1.0, prod_level=1.0, t=0.0, nivel=1):
    glPushMatrix()
    glScalef(scale, scale, scale)
    
    # Main tanks
    for i in range(2 + nivel // 2):
        glPushMatrix()
        glTranslatef(-0.7 + i * 0.8, 0.6, 0)
        glColor3f(0.35 + i * 0.05, 0.35, 0.4)
        draw_cylinder(0.35, 1.2 + i * 0.15, 10)
        glPopMatrix()
    
    # Processing unit
    glColor3f(0.3, 0.32, 0.35)
    draw_box(1.8, 0.8, 1.2)
    
    # Pipes
    glColor3f(0.5, 0.5, 0.52)
    for i in range(3):
        glPushMatrix()
        glTranslatef(-0.6 + i * 0.6, 0.5, 0.65)
        glRotatef(90, 1, 0, 0)
        draw_cylinder(0.08, 0.4, 6)
        glPopMatrix()
    
    glPopMatrix()
    
    # Flame on top (when producing)
    if prod_level > 0.3:
        glDisable(GL_LIGHTING)
        glPushMatrix()
        glTranslatef(0.7 * scale, 1.5 * scale, 0)
        
        flame_height = 0.2 + 0.15 * math.sin(t * 8) * prod_level
        glColor4f(1.0, 0.5, 0.1, 0.9)
        glScalef(0.1, flame_height, 0.1)
        draw_box(1, 1, 1)
        
        glColor4f(1.0, 0.8, 0.2, 0.7)
        glTranslatef(0, 0.3, 0)
        glScalef(0.7, 0.5, 0.7)
        draw_box(1, 1, 1)
        
        glPopMatrix()
        glEnable(GL_LIGHTING)

def draw_gold_mine(scale=1.0, prod_level=1.0, t=0.0, nivel=1):
    glPushMatrix()
    glScalef(scale, scale, scale)
    
    # Mine entrance
    glColor3f(0.45, 0.35, 0.25)
    draw_box(1.5, 1.2, 1.0)
    
    # Entrance arch
    glPushMatrix()
    glTranslatef(0, 0.6, 0.51)
    glColor3f(0.55, 0.45, 0.2)
    draw_prism_triangle(1.0, 0.5, 0.1)
    glPopMatrix()
    
    # Support beams
    glColor3f(0.4, 0.3, 0.2)
    for x in [-0.6, 0.6]:
        glPushMatrix()
        glTranslatef(x, 0, 0.52)
        glScalef(0.1, 1.2, 0.1)
        draw_box(1, 1, 1)
        glPopMatrix()
    
    # Gold veins (decorative)
    glDisable(GL_LIGHTING)
    glColor3f(0.9, 0.75, 0.1)
    for i in range(nivel):
        glPushMatrix()
        x = -0.3 + (i % 3) * 0.3
        y = 0.2 + (i // 3) * 0.3
        glTranslatef(x, y, 0.52)
        size = 0.08 + 0.02 * math.sin(t * 2 + i)
        glScalef(size, size, 0.02)
        draw_box(1, 1, 1)
        glPopMatrix()
    glEnable(GL_LIGHTING)
    
    glPopMatrix()
    
    # Mining cart with gold
    glPushMatrix()
    cart_pos = math.sin(t * 1.5) * 0.8 * prod_level
    glTranslatef(cart_pos, 0.15 * scale, 0.8 * scale)
    
    # Cart body
    glColor3f(0.4, 0.35, 0.3)
    glScalef(0.4 * scale, 0.25 * scale, 0.3 * scale)
    draw_box(1, 1, 1)
    
    # Gold in cart
    glColor3f(0.95, 0.8, 0.15)
    glTranslatef(0, 0.6, 0)
    glScalef(0.7, 0.4, 0.7)
    draw_box(1, 1, 1)
    
    glPopMatrix()

def draw_bank(scale=1.0, prod_level=1.0, t=0.0, nivel=1):
    glPushMatrix()
    glScalef(scale, scale * (1 + nivel * 0.1), scale)
    
    # Main building (classic style)
    glColor3f(0.55, 0.55, 0.58)
    draw_box(2.0, 1.5, 1.4)
    
    # Columns
    glColor3f(0.65, 0.65, 0.68)
    for x in [-0.7, -0.35, 0.35, 0.7]:
        glPushMatrix()
        glTranslatef(x, 0, 0.72)
        draw_cylinder(0.08, 1.4, 8)
        glPopMatrix()
    
    # Pediment (triangular top)
    glPushMatrix()
    glTranslatef(0, 0.95, 0)
    glColor3f(0.6, 0.6, 0.63)
    draw_prism_triangle(2.2, 0.6, 0.3)
    glPopMatrix()
    
    # Door
    glColor3f(0.25, 0.2, 0.15)
    glPushMatrix()
    glTranslatef(0, -0.35, 0.71)
    draw_box(0.5, 0.8, 0.02)
    glPopMatrix()
    
    glPopMatrix()
    
    # Dollar sign (floating, animated)
    glDisable(GL_LIGHTING)
    glPushMatrix()
    y_offset = 1.6 * scale + 0.1 * math.sin(t * 2)
    glTranslatef(0, y_offset, 0)
    
    intensity = 0.6 + 0.4 * math.sin(t * 1.5)
    glColor4f(0.2 * intensity, 0.8 * intensity, 0.3 * intensity, 0.9)
    glScalef(0.2, 0.25, 0.05)
    draw_box(1, 1, 1)
    glPopMatrix()
    glEnable(GL_LIGHTING)

# ═══════════════════════════════════════════════════════════════════════════════
# GL SCENE WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class GLScene(QOpenGLWidget):
    def __init__(self, empresa: Empresa):
        super().__init__()
        self.empresa = empresa
        self.camera_angle = [30.0, -30.0]
        self.camera_target_angle = [30.0, -30.0]
        self.zoom = 45.0
        self.target_zoom = 45.0
        self.last_pos = None
        self.time = 0.0
        self.setMinimumSize(600, 400)
        
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Ambient light
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        
        # Main light (sun)
        glLightfv(GL_LIGHT0, GL_POSITION, [15, 25, 15, 0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.95, 0.85, 1])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.5, 0.5, 0.4, 1])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.15, 0.15, 0.2, 1])
        
        # Fill light
        glLightfv(GL_LIGHT1, GL_POSITION, [-10, 10, -5, 0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.3, 0.35, 0.4, 1])
        
        # Material properties
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.3, 0.3, 0.3, 1])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 30)
        
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h if h > 0 else 1)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.zoom, w / (h if h > 0 else 1), 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
        
    def paintGL(self):
        self.time += 0.025
        
        # Smooth camera movement
        self.camera_angle[0] += (self.camera_target_angle[0] - self.camera_angle[0]) * 0.15
        self.camera_angle[1] += (self.camera_target_angle[1] - self.camera_angle[1]) * 0.15
        self.zoom += (self.target_zoom - self.zoom) * 0.1
        
        # Draw gradient sky
        self.draw_sky_gradient()
        
        glClear(GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        r = 40.0
        alt = math.radians(self.camera_angle[0])
        az = math.radians(self.camera_angle[1])
        eyex = r * math.cos(alt) * math.cos(az)
        eyey = r * math.sin(alt)
        eyez = r * math.cos(alt) * math.sin(az)
        gluLookAt(eyex, eyey, eyez, 0, 0, 0, 0, 1, 0)
        
        self.draw_ground()
        self.draw_grid()
        self.draw_constructions()
        
    def draw_sky_gradient(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw fullscreen quad with gradient
        glBegin(GL_QUADS)
        # Top color (darker blue)
        glColor3f(0.05, 0.1, 0.2)
        glVertex2f(-1, 1)
        glVertex2f(1, 1)
        # Bottom color (lighter blue/purple)
        glColor3f(0.15, 0.2, 0.35)
        glVertex2f(1, -1)
        glVertex2f(-1, -1)
        glEnd()
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
    def draw_ground(self):
        glDisable(GL_LIGHTING)
        
        # Main ground (grass)
        glColor3f(0.08, 0.15, 0.08)
        glBegin(GL_QUADS)
        glVertex3f(-80, -0.02, -80)
        glVertex3f(80, -0.02, -80)
        glVertex3f(80, -0.02, 80)
        glVertex3f(-80, -0.02, 80)
        glEnd()
        
        # Construction area (darker)
        glColor3f(0.06, 0.08, 0.06)
        glBegin(GL_QUADS)
        glVertex3f(-20, -0.01, -15)
        glVertex3f(20, -0.01, -15)
        glVertex3f(20, -0.01, 15)
        glVertex3f(-20, -0.01, 15)
        glEnd()
        
        glEnable(GL_LIGHTING)
        
    def draw_grid(self):
        glDisable(GL_LIGHTING)
        glColor3f(0.12, 0.18, 0.12)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        step = 4
        for i in range(-40, 41, step):
            glVertex3f(i, 0, -40)
            glVertex3f(i, 0, 40)
            glVertex3f(-40, 0, i)
            glVertex3f(40, 0, i)
        glEnd()
        glEnable(GL_LIGHTING)
        
    def draw_constructions(self):
        gap = 6.5
        cols = 6
        
        for idx, c in enumerate(self.empresa.construcoes):
            modelo = c.modelo
            col = idx % cols
            row = idx // cols
            x = (col - (cols - 1) / 2) * gap
            z = (row - 1) * gap
            
            # Calculate production level
            prod_level = 0.0
            if modelo.producao_recurso:
                rec = self.empresa.recursos.get(modelo.producao_recurso)
                if rec:
                    prod_level = min(1.0, rec.quantidade / 200.0)
            else:
                prod_level = 0.5  # Default for non-producing buildings
            
            glPushMatrix()
            glTranslatef(x, 0, z)
            
            # Draw appropriate model
            draw_funcs = {
                'madeira': draw_factory,
                'metal': draw_mine,
                'energia': draw_hydro,
                'cafe': draw_coffee,
                'pesquisa': draw_research,
                'petroleo': draw_refinery,
                'ouro': draw_gold_mine,
                'banco': draw_bank,
            }
            
            func = draw_funcs.get(modelo.id)
            if func:
                func(scale=1.1, prod_level=prod_level, t=self.time, nivel=c.nivel)
            else:
                # Fallback cube
                glColor3f(*modelo.cor_principal)
                draw_box(1.5, 1.5, 1.5)
            
            # Level indicator above building
            self.draw_level_indicator(c.nivel, modelo.nivel_max)
            
            glPopMatrix()
    
    def draw_level_indicator(self, nivel, nivel_max):
        glDisable(GL_LIGHTING)
        glPushMatrix()
        glTranslatef(0, 2.5, 0)
        
        # Draw stars for level
        for i in range(nivel):
            glPushMatrix()
            glTranslatef(-0.3 * (nivel - 1) / 2 + i * 0.3, 0, 0)
            glColor3f(1.0, 0.85, 0.2)
            draw_box(0.15, 0.15, 0.02)
            glPopMatrix()
        
        glPopMatrix()
        glEnable(GL_LIGHTING)
        
    def mousePressEvent(self, event):
        self.last_pos = event.position()
        
    def mouseMoveEvent(self, event):
        if not self.last_pos:
            return
        dx = event.position().x() - self.last_pos.x()
        dy = event.position().y() - self.last_pos.y()
        
        if event.buttons() & QtCore.Qt.LeftButton:
            self.camera_target_angle[1] += dx * 0.4
            self.camera_target_angle[0] -= dy * 0.3
            self.camera_target_angle[0] = max(-89, min(89, self.camera_target_angle[0]))
        
        self.last_pos = event.position()
        self.update()
        
    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120.0
        self.target_zoom -= delta * 3.0
        self.target_zoom = max(20, min(80, self.target_zoom))
        self.resizeGL(self.width(), self.height())
        self.update()

# ═══════════════════════════════════════════════════════════════════════════════
# PRICE CHART WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class PriceChartWidget(QWidget):
    def __init__(self, empresa: Empresa):
        super().__init__()
        self.empresa = empresa
        self.selected_resource = 'madeira'
        self.setMinimumHeight(150)
        self.setMaximumHeight(200)
        
    def set_resource(self, resource_key: str):
        self.selected_resource = resource_key
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(22, 33, 62))
        
        rec = self.empresa.recursos.get(self.selected_resource)
        if not rec or len(rec.preco_historico) < 2:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignCenter, "Dados insuficientes")
            return
        
        prices = rec.preco_historico[-30:]  # Last 30 data points
        
        margin = 40
        w = self.width() - margin * 2
        h = self.height() - margin * 2
        
        if not prices:
            return
            
        min_price = min(prices) * 0.9
        max_price = max(prices) * 1.1
        price_range = max_price - min_price if max_price != min_price else 1
        
        # Draw axes
        painter.setPen(QPen(QColor(100, 100, 120), 1))
        painter.drawLine(margin, margin, margin, self.height() - margin)
        painter.drawLine(margin, self.height() - margin, self.width() - margin, self.height() - margin)
        
        # Draw price labels
        painter.setPen(QColor(150, 150, 170))
        painter.setFont(QFont('Arial', 8))
        painter.drawText(5, margin + 5, f"R${max_price:.1f}")
        painter.drawText(5, self.height() - margin, f"R${min_price:.1f}")
        
        # Draw chart line
        if len(prices) > 1:
            points = []
            for i, price in enumerate(prices):
                x = margin + (i / (len(prices) - 1)) * w
                y = self.height() - margin - ((price - min_price) / price_range) * h
                points.append((x, y))
            
            # Gradient line
            gradient = QLinearGradient(0, margin, 0, self.height() - margin)
            gradient.setColorAt(0, QColor(79, 195, 247))
            gradient.setColorAt(1, QColor(0, 137, 123))
            
            pen = QPen(QBrush(gradient), 2)
            painter.setPen(pen)
            
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]), 
                               int(points[i+1][0]), int(points[i+1][1]))
            
            # Draw dots at data points
            painter.setBrush(QColor(79, 195, 247))
            painter.setPen(Qt.NoPen)
            for x, y in points[-5:]:  # Only last 5 dots
                painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)
        
        # Title
        painter.setPen(QColor(200, 200, 220))
        painter.setFont(QFont('Arial', 10, QFont.Bold))
        painter.drawText(margin, 20, f"{rec.simbolo} {rec.nome} - Histórico de Preços")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏭 Simulador Econômico 3D — Enhanced Edition")
        self.resize(1200, 700)
        self.empresa = Empresa()
        
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)  # 20 FPS for smooth animation
        
        self.update_all()
        
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left panel
        left_panel = QWidget()
        left_panel.setFixedWidth(470)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        
        # Title
        title = QLabel("🏭 Simulador Econômico 3D")
        title.setObjectName("title")
        left_layout.addWidget(title)
        
        # Stats cards
        stats_layout = QGridLayout()
        stats_layout.setSpacing(8)
        
        self.card_capital = self.create_stat_card("💰 Capital", "R$ 15.000,00")
        self.card_turno = self.create_stat_card("📅 Turno", "1")
        self.card_pesquisa = self.create_stat_card("🔬 Pesquisa", "0")
        self.card_manut = self.create_stat_card("🔧 Manutenção", "R$ 0,00")
        
        stats_layout.addWidget(self.card_capital, 0, 0)
        stats_layout.addWidget(self.card_turno, 0, 1)
        stats_layout.addWidget(self.card_pesquisa, 1, 0)
        stats_layout.addWidget(self.card_manut, 1, 1)
        left_layout.addLayout(stats_layout)
        
        # Tabs
        tabs = QTabWidget()
        
        # Resources tab
        resources_tab = QWidget()
        res_layout = QVBoxLayout(resources_tab)
        
        res_label = QLabel("📦 Recursos")
        res_label.setObjectName("sectionTitle")
        res_layout.addWidget(res_label)
        
        self.lst_recursos = QListWidget()
        self.lst_recursos.setMaximumHeight(180)
        res_layout.addWidget(self.lst_recursos)
        
        # Trade controls
        trade_group = QGroupBox("Negociar")
        trade_layout = QGridLayout(trade_group)
        
        self.cmb_recurso = QComboBox()
        self.cmb_recurso.setToolTip("Selecione o recurso")
        trade_layout.addWidget(QLabel("Recurso:"), 0, 0)
        trade_layout.addWidget(self.cmb_recurso, 0, 1)
        
        self.spn_quantidade = QSpinBox()
        self.spn_quantidade.setRange(1, 100000)
        self.spn_quantidade.setValue(10)
        self.spn_quantidade.setToolTip("Quantidade para comprar/vender")
        trade_layout.addWidget(QLabel("Quantidade:"), 1, 0)
        trade_layout.addWidget(self.spn_quantidade, 1, 1)
        
        btn_layout = QHBoxLayout()
        self.btn_comprar = QPushButton("🛒 Comprar")
        self.btn_comprar.setObjectName("successBtn")
        self.btn_vender = QPushButton("📤 Vender")
        self.btn_vender.setObjectName("actionBtn")
        btn_layout.addWidget(self.btn_comprar)
        btn_layout.addWidget(self.btn_vender)
        trade_layout.addLayout(btn_layout, 2, 0, 1, 2)
        
        self.btn_vender_tudo = QPushButton("💰 Vender Tudo")
        self.btn_vender_tudo.setObjectName("dangerBtn")
        trade_layout.addWidget(self.btn_vender_tudo, 3, 0, 1, 2)
        
        res_layout.addWidget(trade_group)
        
        # Price chart
        self.price_chart = PriceChartWidget(self.empresa)
        res_layout.addWidget(self.price_chart)
        
        tabs.addTab(resources_tab, "📦 Recursos")
        
        # Buildings tab
        buildings_tab = QWidget()
        build_layout = QVBoxLayout(buildings_tab)
        
        build_label = QLabel("🏗️ Construções Disponíveis")
        build_label.setObjectName("sectionTitle")
        build_layout.addWidget(build_label)
        
        self.lst_modelos = QListWidget()
        self.lst_modelos.setMaximumHeight(200)
        build_layout.addWidget(self.lst_modelos)
        
        self.btn_construir = QPushButton("🏗️ Construir Selecionado")
        self.btn_construir.setObjectName("successBtn")
        build_layout.addWidget(self.btn_construir)
        
        # My buildings
        my_build_label = QLabel("🏭 Minhas Construções")
        my_build_label.setObjectName("sectionTitle")
        build_layout.addWidget(my_build_label)
        
        self.lst_minhas = QListWidget()
        self.lst_minhas.setMaximumHeight(150)
        build_layout.addWidget(self.lst_minhas)
        
        mybuild_btns = QHBoxLayout()
        self.btn_upgrade = QPushButton("⬆️ Upgrade")
        self.btn_upgrade.setObjectName("actionBtn")
        self.btn_demolir = QPushButton("🗑️ Demolir")
        self.btn_demolir.setObjectName("dangerBtn")
        mybuild_btns.addWidget(self.btn_upgrade)
        mybuild_btns.addWidget(self.btn_demolir)
        build_layout.addLayout(mybuild_btns)
        
        tabs.addTab(buildings_tab, "🏗️ Construções")
        
        # Events tab
        events_tab = QWidget()
        events_layout = QVBoxLayout(events_tab)
        
        events_label = QLabel("📰 Eventos Recentes")
        events_label.setObjectName("sectionTitle")
        events_layout.addWidget(events_label)
        
        self.lst_eventos = QListWidget()
        events_layout.addWidget(self.lst_eventos)
        
        tabs.addTab(events_tab, "📰 Eventos")
        
        # Achievements tab
        achieve_tab = QWidget()
        achieve_layout = QVBoxLayout(achieve_tab)
        
        achieve_label = QLabel("🏆 Conquistas")
        achieve_label.setObjectName("sectionTitle")
        achieve_layout.addWidget(achieve_label)
        
        self.lst_conquistas = QListWidget()
        achieve_layout.addWidget(self.lst_conquistas)
        
        tabs.addTab(achieve_tab, "🏆 Conquistas")
        
        left_layout.addWidget(tabs)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.btn_turno = QPushButton("⏭️ Próximo Turno (Space)")
        self.btn_turno.setObjectName("successBtn")
        self.btn_turno.setMinimumHeight(40)
        action_layout.addWidget(self.btn_turno)
        left_layout.addLayout(action_layout)
        
        # Save/Load buttons
        file_layout = QHBoxLayout()
        self.btn_salvar = QPushButton("💾 Salvar")
        self.btn_carregar = QPushButton("📂 Carregar")
        file_layout.addWidget(self.btn_salvar)
        file_layout.addWidget(self.btn_carregar)
        left_layout.addLayout(file_layout)
        
        main_layout.addWidget(left_panel)
        
        # GL Scene
        self.gl = GLScene(self.empresa)
        main_layout.addWidget(self.gl, 1)
        
        # Populate combos
        self.populate_combos()
        
    def create_stat_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #81d4fa; font-size: 11px;")
        
        value_lbl = QLabel(value)
        value_lbl.setStyleSheet("color: #eaeaea; font-size: 16px; font-weight: bold;")
        value_lbl.setObjectName("value")
        
        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        
        return card
        
    def populate_combos(self):
        self.cmb_recurso.clear()
        for key, rec in self.empresa.recursos.items():
            self.cmb_recurso.addItem(f"{rec.simbolo} {rec.nome}", key)
        
        self.update_modelos()
        
    def setup_connections(self):
        self.btn_turno.clicked.connect(self.on_turno)
        self.btn_comprar.clicked.connect(self.on_comprar)
        self.btn_vender.clicked.connect(self.on_vender)
        self.btn_vender_tudo.clicked.connect(self.on_vender_tudo)
        self.btn_construir.clicked.connect(self.on_construir)
        self.btn_upgrade.clicked.connect(self.on_upgrade)
        self.btn_demolir.clicked.connect(self.on_demolir)
        self.btn_salvar.clicked.connect(self.on_salvar)
        self.btn_carregar.clicked.connect(self.on_carregar)
        self.cmb_recurso.currentIndexChanged.connect(self.on_recurso_changed)
        
    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Space), self, self.on_turno)
        QShortcut(QKeySequence("Ctrl+S"), self, self.on_salvar)
        QShortcut(QKeySequence("Ctrl+O"), self, self.on_carregar)
        
    def fmoney(self, v: float) -> str:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def tick(self):
        self.gl.update()
        
    def update_all(self):
        # Update stat cards
        self.card_capital.findChild(QLabel, "value").setText(self.fmoney(self.empresa.capital))
        self.card_turno.findChild(QLabel, "value").setText(str(self.empresa.turno))
        self.card_pesquisa.findChild(QLabel, "value").setText(str(self.empresa.pontos_pesquisa))
        self.card_manut.findChild(QLabel, "value").setText(self.fmoney(self.empresa.custo_manutencao_total()))
        
        self.update_recursos()
        self.update_modelos()
        self.update_minhas_construcoes()
        self.update_eventos()
        self.update_conquistas()
        self.price_chart.update()
        self.gl.update()
        
    def update_recursos(self):
        self.lst_recursos.clear()
        for key, r in self.empresa.recursos.items():
            trend = ""
            if len(r.preco_historico) >= 2:
                diff = r.preco - r.preco_historico[-2]
                if diff > 0:
                    trend = " 📈"
                elif diff < 0:
                    trend = " 📉"
            
            item = QListWidgetItem(f"{r.simbolo} {r.nome:<10} | Qtd: {r.quantidade:>6} | {self.fmoney(r.preco)}{trend}")
            
            # Color based on quantity
            if r.quantidade < 20:
                item.setForeground(QColor(255, 100, 100))
            elif r.quantidade > 200:
                item.setForeground(QColor(100, 255, 100))
            
            self.lst_recursos.addItem(item)
            
    def update_modelos(self):
        self.lst_modelos.clear()
        for mid, m in self.empresa.modelos_construcao.items():
            item = QListWidgetItem(f"{m.simbolo} {m.nome} — {self.fmoney(m.custo)}")
            item.setData(Qt.UserRole, mid)
            item.setToolTip(m.descricao)
            
            # Gray out if can't afford
            if self.empresa.capital < m.custo:
                item.setForeground(QColor(100, 100, 100))
            
            self.lst_modelos.addItem(item)
            
    def update_minhas_construcoes(self):
        self.lst_minhas.clear()
        for idx, c in enumerate(self.empresa.construcoes):
            nivel_str = "⭐" * c.nivel
            item = QListWidgetItem(
                f"{c.modelo.simbolo} {c.modelo.nome} [{nivel_str}] — Manut: {self.fmoney(c.manutencao_atual)}"
            )
            item.setData(Qt.UserRole, idx)
            
            if c.nivel >= c.modelo.nivel_max:
                item.setForeground(QColor(255, 215, 0))  # Gold for max level
            
            self.lst_minhas.addItem(item)
            
    def update_eventos(self):
        self.lst_eventos.clear()
        for ev in self.empresa.eventos_log:
            color_map = {
                'bonus': QColor(100, 200, 100),
                'penalty': QColor(255, 100, 100),
                'neutral': QColor(150, 150, 200),
                'special': QColor(255, 215, 0),
            }
            item = QListWidgetItem(f"{ev.icone} {ev.titulo}: {ev.descricao}")
            item.setForeground(color_map.get(ev.tipo, QColor(200, 200, 200)))
            self.lst_eventos.addItem(item)
            
    def update_conquistas(self):
        self.lst_conquistas.clear()
        for c in self.empresa.conquistas.values():
            if c.desbloqueada:
                item = QListWidgetItem(f"✅ {c.icone} {c.nome} — {c.descricao}")
                item.setForeground(QColor(100, 255, 100))
            else:
                item = QListWidgetItem(f"🔒 {c.icone} {c.nome} — {c.descricao}")
                item.setForeground(QColor(100, 100, 100))
            self.lst_conquistas.addItem(item)
    
    # Event handlers
    def on_turno(self):
        eventos, conquistas = self.empresa.avancar_turno()
        self.update_all()
        
        # Show achievement notifications
        for c in conquistas:
            QMessageBox.information(
                self, "🏆 Conquista Desbloqueada!",
                f"{c.icone} {c.nome}\n\n{c.descricao}"
            )
        
        # Show critical events
        for ev in eventos:
            if ev.tipo in ['bonus', 'penalty']:
                icon = QMessageBox.Information if ev.tipo == 'bonus' else QMessageBox.Warning
                QMessageBox.information(self, ev.titulo, ev.descricao)
                
    def on_comprar(self):
        chave = self.cmb_recurso.currentData()
        qtd = self.spn_quantidade.value()
        
        try:
            self.empresa.comprar_recurso(chave, qtd)
            self.update_all()
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))
            
    def on_vender(self):
        chave = self.cmb_recurso.currentData()
        qtd = self.spn_quantidade.value()
        
        try:
            self.empresa.vender_recurso(chave, qtd)
            self.update_all()
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))
            
    def on_vender_tudo(self):
        total = sum(r.quantidade * r.preco for r in self.empresa.recursos.values())
        
        if total == 0:
            QMessageBox.information(self, "Info", "Não há recursos para vender.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Venda",
            f"Vender todos os recursos por {self.fmoney(total)}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for r in self.empresa.recursos.values():
                self.empresa.estatisticas['total_ganho'] += r.quantidade * r.preco
                self.empresa.estatisticas['recursos_vendidos'] += r.quantidade
                r.quantidade = 0
            self.empresa.capital += total
            QMessageBox.information(self, "Venda Completa", f"Receita: {self.fmoney(total)}")
            self.update_all()
            
    def on_construir(self):
        item = self.lst_modelos.currentItem()
        if not item:
            QMessageBox.warning(self, "Erro", "Selecione uma construção.")
            return
        
        modelo_id = item.data(Qt.UserRole)
        
        try:
            self.empresa.construir(modelo_id)
            self.update_all()
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))
            
    def on_upgrade(self):
        item = self.lst_minhas.currentItem()
        if not item:
            QMessageBox.warning(self, "Erro", "Selecione uma construção.")
            return
        
        idx = item.data(Qt.UserRole)
        c = self.empresa.construcoes[idx]
        
        if c.nivel >= c.modelo.nivel_max:
            QMessageBox.information(self, "Info", "Esta construção já está no nível máximo!")
            return
        
        custo = c.custo_upgrade
        reply = QMessageBox.question(
            self, "Confirmar Upgrade",
            f"Fazer upgrade de {c.modelo.nome} para nível {c.nivel + 1}?\n\nCusto: {self.fmoney(custo)}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.empresa.upgrade_construcao(idx)
                self.update_all()
            except ValueError as e:
                QMessageBox.warning(self, "Erro", str(e))
                
    def on_demolir(self):
        item = self.lst_minhas.currentItem()
        if not item:
            QMessageBox.warning(self, "Erro", "Selecione uma construção.")
            return
        
        idx = item.data(Qt.UserRole)
        c = self.empresa.construcoes[idx]
        reembolso = c.modelo.custo * 0.3
        
        reply = QMessageBox.question(
            self, "Confirmar Demolição",
            f"Demolir {c.modelo.nome}?\n\nReembolso: {self.fmoney(reembolso)} (30%)",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.empresa.demolir_construcao(idx)
            self.update_all()
            
    def on_recurso_changed(self):
        chave = self.cmb_recurso.currentData()
        if chave:
            self.price_chart.set_resource(chave)
            
    def on_salvar(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Jogo", "", "JSON Files (*.json)"
        )
        
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.empresa.to_dict(), f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Sucesso", "Jogo salvo com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
                
    def on_carregar(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Carregar Jogo", "", "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.empresa.from_dict(data)
                self.update_all()
                QMessageBox.information(self, "Sucesso", "Jogo carregado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    fmt = QSurfaceFormat()
    fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
    fmt.setVersion(2, 1)
    fmt.setSamples(4)  # Anti-aliasing
    QSurfaceFormat.setDefaultFormat(fmt)
    
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    
    win = MainWindow()
    win.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
