"""
Script para generar outputs de ejemplo realistas de MiaplPy.
Simula resultados de procesamiento InSAR con Phase Linking (EMI)
sobre una zona con vegetacion, zona urbana y montana.

Desarrollado para el proyecto SISAR - CEDIAC/UNCUYO/CONICET
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path

np.random.seed(42)

OUTPUT_DIR = Path("example_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Parametros de la zona simulada ──────────────────────────────────────────
LON_MIN, LON_MAX = -69.0, -67.0
LAT_MIN, LAT_MAX = -33.0, -31.0
N_PUNTOS = 8000   # puntos PS/DS detectados por MiaplPy
N_FECHAS = 60     # imagenes Sentinel-1 (~2 anios, cada 12 dias)
DIAS = np.arange(0, N_FECHAS * 12, 12)


def simular_zona():
    """
    Genera puntos PS/DS con coherencia y velocidad simuladas.
    Divide la zona en:
      - Zona urbana  (alta coherencia, deformacion variable)
      - Zona de cultivos (coherencia media, casi estable)
      - Montana      (coherencia baja, pocos puntos)
      - Subsidencia  (hundimiento localizado, ej: extraccion de agua)
    """
    lons = np.random.uniform(LON_MIN, LON_MAX, N_PUNTOS)
    lats = np.random.uniform(LAT_MIN, LAT_MAX, N_PUNTOS)

    velocidad = np.zeros(N_PUNTOS)
    coherencia = np.zeros(N_PUNTOS)
    zona = np.full(N_PUNTOS, 'otro', dtype=object)

    for i in range(N_PUNTOS):
        lo, la = lons[i], lats[i]

        # Montana (noroeste) - coherencia muy baja, casi sin puntos
        if lo < -68.2 and la > -31.8:
            coherencia[i] = np.random.uniform(0.1, 0.35)
            velocidad[i] = np.random.normal(0, 2)
            zona[i] = 'montana'

        # Zona urbana (centro-este) - coherencia alta
        elif -68.3 < lo < -67.5 and -32.5 < la < -31.8:
            coherencia[i] = np.random.uniform(0.6, 0.95)
            velocidad[i] = np.random.normal(-2, 1.5)
            zona[i] = 'urbana'

        # Subsidencia localizada (ej: extraccion de agua subterranea)
        elif abs(lo - (-67.8)) < 0.25 and abs(la - (-32.3)) < 0.2:
            coherencia[i] = np.random.uniform(0.5, 0.85)
            dist = np.sqrt((lo + 67.8)**2 + (la + 32.3)**2)
            velocidad[i] = -18 * np.exp(-dist / 0.08) + np.random.normal(0, 1)
            zona[i] = 'subsidencia'

        # Cultivos (sur) - coherencia media, estacional
        elif la < -32.3:
            coherencia[i] = np.random.uniform(0.25, 0.6)
            velocidad[i] = np.random.normal(0.5, 1.2)
            zona[i] = 'cultivos'

        # Resto
        else:
            coherencia[i] = np.random.uniform(0.2, 0.55)
            velocidad[i] = np.random.normal(-1, 2)
            zona[i] = 'otro'

    # Filtrar puntos con baja coherencia (MiaplPy los descarta)
    umbral = 0.35
    mask = coherencia >= umbral

    return lons[mask], lats[mask], velocidad[mask], coherencia[mask], zona[mask]


def plot_velocity_map(lons, lats, velocidad, zona):
    """Mapa de velocidad LOS con puntos PS/DS."""

    fig, ax = plt.subplots(figsize=(11, 9))
    ax.set_facecolor('#d4e6f1')  # fondo azul agua

    # Zonas de fondo
    urbana = mpatches.FancyBboxPatch((-68.3, -32.5), 0.8, 0.7,
                                      boxstyle="round,pad=0.02",
                                      linewidth=1, edgecolor='gray',
                                      facecolor='#f5cba7', alpha=0.3,
                                      label='Zona urbana')
    cultivos = mpatches.FancyBboxPatch((-69.0, -33.0), 2.0, 0.7,
                                        boxstyle="round,pad=0.02",
                                        linewidth=1, edgecolor='gray',
                                        facecolor='#a9dfbf', alpha=0.3,
                                        label='Cultivos')
    montana = mpatches.FancyBboxPatch((-69.0, -31.8), 0.8, 0.8,
                                       boxstyle="round,pad=0.02",
                                       linewidth=1, edgecolor='gray',
                                       facecolor='#d5d8dc', alpha=0.3,
                                       label='Montana')
    ax.add_patch(urbana)
    ax.add_patch(cultivos)
    ax.add_patch(montana)

    # Scatter de puntos PS/DS coloreados por velocidad
    norm = TwoSlopeNorm(vmin=-20, vcenter=0, vmax=8)
    sc = ax.scatter(lons, lats,
                    c=velocidad,
                    cmap='RdYlBu',
                    norm=norm,
                    s=4,
                    alpha=0.7,
                    linewidths=0)

    cbar = plt.colorbar(sc, ax=ax, shrink=0.75, pad=0.02)
    cbar.set_label('Velocidad LOS (mm/año)', fontsize=12)
    cbar.ax.tick_params(labelsize=10)

    # Marcadores de referencia
    ax.plot(-67.8, -32.3, 'v', color='black', markersize=14,
            zorder=5, label='Subsidencia máx: ~-18 mm/año')
    ax.annotate('Subsidencia\n-18 mm/año',
                xy=(-67.8, -32.3), xytext=(-68.1, -32.1),
                fontsize=9, color='black',
                arrowprops=dict(arrowstyle='->', color='black'))

    # Punto de referencia GPS (estable)
    ax.plot(-68.8, -31.6, '*', color='gold', markersize=14,
            zorder=5, markeredgecolor='black', label='Punto ref. GPS (estable)')

    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.set_xlabel('Longitud (°)', fontsize=11)
    ax.set_ylabel('Latitud (°)', fontsize=11)
    ax.set_title(
        'Mapa de Velocidad de Deformación — MiaplPy (Phase Linking EMI)\n'
        'Sentinel-1 Ascending | 2022-2023 | Mendoza, Argentina',
        fontsize=12, fontweight='bold'
    )
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    legend_patches = [
        mpatches.Patch(facecolor='#f5cba7', alpha=0.6, label='Zona urbana'),
        mpatches.Patch(facecolor='#a9dfbf', alpha=0.6, label='Cultivos'),
        mpatches.Patch(facecolor='#d5d8dc', alpha=0.6, label='Montana'),
        plt.Line2D([0], [0], marker='v', color='w', markerfacecolor='black',
                   markersize=10, label='Subsidencia máx'),
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='gold',
                   markeredgecolor='black', markersize=12, label='Ref. GPS'),
    ]
    ax.legend(handles=legend_patches, loc='lower left', fontsize=9,
              framealpha=0.9)

    # Texto informativo
    n_puntos = len(lons)
    ax.text(0.02, 0.98,
            f'Puntos PS/DS detectados: {n_puntos:,}\n'
            f'Método: Phase Linking EMI\n'
            f'Imágenes procesadas: {N_FECHAS}\n'
            f'Período: Ene 2022 – Dic 2023',
            transform=ax.transAxes,
            fontsize=8, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.85))

    plt.tight_layout()
    out = OUTPUT_DIR / "velocity_map.png"
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Mapa de velocidad guardado: {out}")


def plot_timeseries(lons, lats, velocidad):
    """
    Serie temporal para 3 puntos representativos:
    subsidencia, zona urbana estable, cultivos.
    """
    # Punto A: subsidencia maxima
    idx_sub = np.argmin(velocidad)
    v_sub = velocidad[idx_sub]

    # Punto B: zona urbana estable
    mask_urb = (lons > -68.3) & (lons < -67.5) & \
               (lats > -32.5) & (lats < -31.8)
    idx_urb = np.where(mask_urb)[0]
    idx_urb = idx_urb[np.argmin(np.abs(velocidad[idx_urb] - (-1.5)))]
    v_urb = velocidad[idx_urb]

    # Punto C: cultivos
    mask_cult = lats < -32.4
    idx_cult = np.where(mask_cult)[0][0]
    v_cult = velocidad[idx_cult]

    def ts(vel, noise_std=1.2, seasonal_amp=3):
        ts = (vel / 365) * DIAS
        ts += seasonal_amp * np.sin(2 * np.pi * DIAS / 365)
        ts += np.random.normal(0, noise_std, N_FECHAS)
        return ts

    ts_sub  = ts(v_sub, noise_std=1.5, seasonal_amp=2)
    ts_urb  = ts(v_urb, noise_std=0.8, seasonal_amp=1.5)
    ts_cult = ts(v_cult, noise_std=2.0, seasonal_amp=5)

    # Guardar CSV
    csv_path = OUTPUT_DIR / "timeseries.csv"
    with open(csv_path, 'w') as f:
        f.write("dia,subsidencia_mm,urbano_mm,cultivos_mm\n")
        for i in range(N_FECHAS):
            f.write(f"{DIAS[i]},{ts_sub[i]:.2f},{ts_urb[i]:.2f},{ts_cult[i]:.2f}\n")
    print(f"[OK] CSV guardado: {csv_path}")

    # Plot
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True)

    configs = [
        (ts_sub,  f'Punto A — Subsidencia ({v_sub:.1f} mm/año)',  'royalblue',  'v'),
        (ts_urb,  f'Punto B — Zona Urbana ({v_urb:.1f} mm/año)',  'darkorange', 's'),
        (ts_cult, f'Punto C — Cultivos ({v_cult:.1f} mm/año)',     'seagreen',   '^'),
    ]

    for ax, (ts_data, titulo, color, marker) in zip(axes, configs):
        ax.plot(DIAS, ts_data, marker=marker, color=color,
                linewidth=1.5, markersize=4, alpha=0.8)
        ax.axhline(0, color='black', linestyle='--', alpha=0.4, linewidth=1)

        # Tendencia lineal
        z = np.polyfit(DIAS, ts_data, 1)
        p = np.poly1d(z)
        ax.plot(DIAS, p(DIAS), '--', color='red', linewidth=1.5,
                alpha=0.7, label=f'Tendencia: {z[0]*365:.1f} mm/año')

        ax.set_ylabel('Deformación\nLOS (mm)', fontsize=10)
        ax.set_title(titulo, fontsize=10, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.fill_between(DIAS, ts_data, 0,
                        alpha=0.1, color=color)

    axes[-1].set_xlabel('Días desde imagen de referencia', fontsize=11)
    fig.suptitle(
        'Series Temporales de Deformación — MiaplPy (Phase Linking EMI)\n'
        'Sentinel-1 | 2022-2023 | Mendoza, Argentina',
        fontsize=12, fontweight='bold', y=1.01
    )

    plt.tight_layout()
    out = OUTPUT_DIR / "timeseries.png"
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Serie temporal guardada: {out}")


def plot_coherence(lons, lats, coherencia):
    """Mapa de coherencia temporal de los puntos PS/DS."""

    fig, ax = plt.subplots(figsize=(11, 9))
    ax.set_facecolor('#eaecee')

    sc = ax.scatter(lons, lats,
                    c=coherencia,
                    cmap='viridis',
                    vmin=0.35, vmax=1.0,
                    s=4, alpha=0.8,
                    linewidths=0)

    cbar = plt.colorbar(sc, ax=ax, shrink=0.75)
    cbar.set_label('Coherencia temporal γ', fontsize=12)

    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.set_xlabel('Longitud (°)', fontsize=11)
    ax.set_ylabel('Latitud (°)', fontsize=11)
    ax.set_title(
        'Mapa de Coherencia Temporal — MiaplPy (Phase Linking EMI)\n'
        'Sentinel-1 | 2022-2023 | Mendoza, Argentina',
        fontsize=12, fontweight='bold'
    )
    ax.grid(True, alpha=0.3, linestyle='--')

    # Anotaciones de zonas
    ax.text(-68.0, -32.1, 'Zona\nUrbana', fontsize=9,
            ha='center', color='white',
            bbox=dict(facecolor='gray', alpha=0.6, boxstyle='round'))
    ax.text(-68.5, -32.7, 'Cultivos', fontsize=9,
            ha='center', color='white',
            bbox=dict(facecolor='green', alpha=0.6, boxstyle='round'))
    ax.text(-68.7, -31.5, 'Montaña', fontsize=9,
            ha='center', color='white',
            bbox=dict(facecolor='#555', alpha=0.6, boxstyle='round'))

    n = len(lons)
    ax.text(0.02, 0.98,
            f'Puntos con coherencia ≥ 0.35: {n:,}\n'
            f'Umbral aplicado por MiaplPy EMI',
            transform=ax.transAxes, fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.85))

    plt.tight_layout()
    out = OUTPUT_DIR / "coherence_map.png"
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Mapa de coherencia guardado: {out}")


if __name__ == "__main__":
    print("=" * 55)
    print(" SISAR — Generando outputs de ejemplo de MiaplPy")
    print("=" * 55)
    print()

    lons, lats, velocidad, coherencia, zona = simular_zona()
    print(f"Puntos PS/DS detectados: {len(lons):,}")
    print()

    plot_velocity_map(lons, lats, velocidad, zona)
    plot_timeseries(lons, lats, velocidad)
    plot_coherence(lons, lats, coherencia)

    print()
    print(f"Archivos guardados en: {OUTPUT_DIR.absolute()}")
    print("=" * 55)
