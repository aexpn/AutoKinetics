import sys
import json
import subprocess
import tempfile
from pathlib import Path
from PyQt6 import sip 
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsTextItem,
    QGraphicsPathItem, QToolBar, QDockWidget, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QFormLayout, QGraphicsItem, QComboBox, QCheckBox, QFileDialog,
    QInputDialog, QMessageBox, QDialog, QTextEdit, QTabWidget
)
from PyQt6.QtGui import (
    QAction, QIcon, QPen, QBrush, QColor, QPainterPath, QFont, QPainter,
    QKeyEvent, QUndoStack, QUndoCommand, QKeySequence, QActionGroup, QTransform,
    QImage, QPixmap
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, pyqtSignal, QThread, QTimer

# =============================================================================
# 1. HINTERGRUND-THREADS UND DIALOGE
# =============================================================================

class SimulationThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, kin_file_path, sim_time, temp_k, plot_dir):
        super().__init__()
        self.kin_file = str(kin_file_path)
        self.sim_time = sim_time
        self.temp_k = temp_k
        self.plot_dir = plot_dir # Verwendet jetzt ein Verzeichnis
        self.python_executable = sys.executable

    def run(self):
        try:
            backend_script_path = Path(__file__).resolve().parent / "backend_main.py"
            command = [
                self.python_executable, str(backend_script_path), self.kin_file,
                "-t", str(self.sim_time), "-T", str(self.temp_k),
                "--plot_dir", self.plot_dir,
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
            output_data = json.loads(result.stdout)
            if "error" in output_data:
                self.error.emit(output_data["error"])
            else:
                self.finished.emit(output_data)
        except subprocess.CalledProcessError as e:
            self.error.emit(f"Backend-Fehler:\n{e.stderr}")
        except json.JSONDecodeError:
            self.error.emit(f"Fehler beim Parsen der Backend-Ausgabe:\n{result.stdout}")
        except Exception as e:
            self.error.emit(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

class PlotDialog(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simulationsergebnisse")
        self.setMinimumSize(900, 750)
        self.results = results

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.create_overview_tab()
        self.create_analysis_tabs_per_reaction()

    def create_overview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        image_label = QLabel("Konzentrationsverlauf wird geladen...")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        plot_files = self.results.get("plot_files", {})
        concentration_plot_path = plot_files.get("concentration")
        
        if concentration_plot_path and Path(concentration_plot_path).exists():
            pixmap = QPixmap(concentration_plot_path)
            image_label.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            image_label.setText("Konzentrationsplot konnte nicht geladen werden.")

        layout.addWidget(image_label)
        self.tabs.addTab(tab, "Gesamtübersicht (Konzentrationen)")

    def create_analysis_tabs_per_reaction(self):
        analysis = self.results.get("analysis", {})
        plot_files = self.results.get("plot_files", {}).get("analysis_plots", {})

        if not analysis:
            no_analysis_tab = QWidget()
            no_analysis_layout = QVBoxLayout(no_analysis_tab)
            no_analysis_layout.addWidget(QLabel("Keine Analyseergebnisse verfügbar."))
            self.tabs.addTab(no_analysis_tab, "Analyse")
            return

        for rate_label, analysis_data in analysis.items():
            # Haupt-Tab für jede Reaktion (k1, k2, ...)
            reaction_tab = QWidget()
            reaction_layout = QVBoxLayout(reaction_tab)
            
            # Zusammenfassung für diese spezifische Reaktion
            summary_label = self.build_summary_label(rate_label, analysis_data)
            reaction_layout.addWidget(summary_label)

            # Verschachteltes Tab-Widget für 0., 1., 2. Ordnung
            order_tabs = QTabWidget()
            reaction_layout.addWidget(order_tabs)

            orders = ["zero_order", "first_order", "second_order"]
            titles = ["Analyse: 0. Ordnung", "Analyse: 1. Ordnung", "Analyse: 2. Ordnung"]
            
            reaction_plots = plot_files.get(rate_label, {})

            for order, title in zip(orders, titles):
                plot_path = reaction_plots.get(order)
                if plot_path and Path(plot_path).exists():
                    img_tab = QWidget()
                    img_layout = QVBoxLayout(img_tab)
                    image_label = QLabel()
                    image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    pixmap = QPixmap(plot_path)
                    image_label.setPixmap(pixmap.scaled(image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    img_layout.addWidget(image_label)
                    order_tabs.addTab(img_tab, title)
            
            self.tabs.addTab(reaction_tab, f"Analyse: {rate_label}")

    def build_summary_label(self, rate_label, data):
        order_map = {"zero_order": "0. Ordnung", "first_order": "1. Ordnung", "second_order": "2. Ordnung"}
        order = order_map.get(data['best_fit_order'], "unbekannt")
        k_unit = data.get('k_unit', '')
        
        summary_text = (f"<h3>Analyse für Reaktion '{rate_label}'</h3>"
                        f"<b>Analysierter Reaktant:</b> {data['analyzed_reactant']}<br/>"
                        f"<b>Beste Passung:</b> {order} (R² = {data['r_squared']:.4f})<br/>"
                        f"<b>Berechnete Rate k:</b> {data['calculated_k']:.4f} {k_unit}")
        
        label = QLabel(summary_text)
        label.setFixedHeight(100)
        return label


# ... (Rest des Codes von AddCommand bis zum Ende von MainWindow bleibt unverändert, aber muss hier sein) ...
# HINWEIS: Der folgende Code ist identisch zur vorherigen Version, wird aber für die Vollständigkeit der Datei benötigt.

class AddCommand(QUndoCommand):
    def __init__(self, item, scene, description):
        super().__init__(description)
        self.item, self.scene = item, scene
    def redo(self): self.scene.addItem(self.item)
    def undo(self):
        if isinstance(self.item, (ArrowItem, GroupItem)): self.item.detach()
        self.scene.removeItem(self.item)

class DeleteCommand(QUndoCommand):
    def __init__(self, items, scene, description):
        super().__init__(description)
        self.items, self.scene = items, scene
    def redo(self):
        for item in self.items:
            if isinstance(item, (ArrowItem, GroupItem)): item.detach()
            self.scene.removeItem(item)
    def undo(self):
        for item in self.items:
            self.scene.addItem(item)
            if isinstance(item, ArrowItem):
                item.start_item.add_arrow(item); item.end_item.add_arrow(item)

class SpeciesItem(QGraphicsTextItem):
    def __init__(self, text, position, parent=None):
        super().__init__(text, parent)
        self.setPos(position)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges); self.setAcceptHoverEvents(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setDefaultTextColor(QColor("#333")); self.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self._pen, self._brush, self.arrows = QPen(Qt.PenStyle.NoPen), QBrush(QColor("#ffffff")), []
        
        self.formula, self.smiles, self.molar_mass = "unbekannt", "", 0.0
        self.mass, self.moles = 0.0, 0.0
        self.concentration, self.start_concentration = 1.0, 1.0
        self.delta_hf, self.s0, self.gibbs_g0 = 0.0, 0.0, 0.0
        
        self.diffusion_coeff, self.sigma, self.epsilon, self.dipole_moment = 0.0, 0.0, 0.0, 0.0
        self.is_intermediate, self.database_id = False, ""
        self.role = "Reactant/Product"
        self.solubility, self.stability, self.side_reactions_tendency = "", "stabil", ""

    def to_dict(self):
        return {key: getattr(self, key) for key in [
            'formula', 'smiles', 'molar_mass', 'mass', 'moles',
            'concentration', 'start_concentration', 'delta_hf', 's0', 'gibbs_g0',
            'diffusion_coeff', 'sigma', 'epsilon', 'dipole_moment', 'is_intermediate', 'database_id', 
            'role', 'solubility', 'stability', 'side_reactions_tendency'
        ]} | {'name': self.toPlainText(), 'pos': [self.pos().x(), self.pos().y()]}

    @staticmethod
    def from_dict(data):
        item = SpeciesItem(data['name'], QPointF(*data['pos']))
        for key, value in data.items():
            if hasattr(item, key) and key not in ['name', 'pos']:
                setattr(item, key, value)
        return item
    def mouseDoubleClickEvent(self, event):
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus(Qt.FocusReason.MouseFocusReason); super().mouseDoubleClickEvent(event)
    def focusOutEvent(self, event):
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        cursor = self.textCursor(); cursor.clearSelection(); self.setTextCursor(cursor)
        super().focusOutEvent(event)
        for arrow in self.arrows:
            if arrow.isSelected():
                arrow.scene().properties_panel.show_properties(arrow)

    def boundingRect(self): return super().boundingRect().adjusted(-5, -5, 5, 5)
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing); painter.setBrush(self._brush)
        painter.setPen(self._pen); painter.drawRoundedRect(self.boundingRect(), 8, 8)
        super().paint(painter, option, widget)
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for arrow in self.arrows: arrow.update_position()
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged: self.update_visual_state()
        return super().itemChange(change, value)
    def hoverEnterEvent(self, event): self.update_visual_state(hover=True)
    def hoverLeaveEvent(self, event): self.update_visual_state(hover=False)
    def update_visual_state(self, hover=False, arrow_start=False):
        if arrow_start: self._pen = QPen(QColor("#fdc500"), 3, Qt.PenStyle.DashLine)
        elif self.isSelected(): self._pen = QPen(QColor("#007bff"), 2.5)
        elif hover: self._pen = QPen(QColor("#a0c4ff"), 2)
        else: self._pen = QPen(Qt.PenStyle.NoPen)
        self.update()
    def add_arrow(self, arrow): self.arrows.append(arrow)
    def remove_arrow(self, arrow):
        if arrow in self.arrows: self.arrows.remove(arrow)

class StoichiometryItem(QGraphicsTextItem):
    def __init__(self, arrow_item, species_item, parent=None):
        super().__init__(parent)
        self.arrow = arrow_item
        self.species = species_item
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.setDefaultTextColor(QColor("#d90429")) 

        self.update_text()

    def get_role(self):
        return 'reactants' if self.species in self.arrow.get_unique_species('reactants') else 'products'

    def update_text(self):
        role = self.get_role()
        factor = self.arrow.stoichiometry_by_name.get(role, {}).get(self.species.toPlainText(), 1)
        self.setPlainText(str(factor))
        self.setVisible(factor > 1)

    def mouseDoubleClickEvent(self, event):
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        cursor = self.textCursor(); cursor.clearSelection(); self.setTextCursor(cursor)
        
        try:
            new_factor = int(self.toPlainText())
            if new_factor > 0:
                self.arrow.update_stoichiometry_from_canvas(self.species, new_factor)
                self.setVisible(new_factor > 1)
            else:
                self.update_text()
        except ValueError:
            self.update_text()
        super().focusOutEvent(event)


class ArrowItem(QGraphicsPathItem):
    def __init__(self, start_item, end_item, rate_constant="k", parent=None):
        super().__init__(parent); self.start_item, self.end_item = start_item, end_item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable); self.rate_constant, self.arrow_type = rate_constant, "Forward"
        pen = QPen(QColor("#444"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin); self.setPen(pen)
        self.start_item.add_arrow(self); self.end_item.add_arrow(self); self.label = QGraphicsTextItem(self.rate_constant, self)
        self.label.setDefaultTextColor(QColor("#c1121f")); self.label.setFont(QFont("Arial", 10)); self.reaction_string, self.reaction_order = "", "1"
        self.temperature_min, self.temperature_max, self.pressure = 500.0, 2000.0, 101325.0
        self.arrhenius_A, self.temperature_exponent_n, self.activation_energy_Ea = 1.0, 0.0, 0.0
        self.rate_expression = "k = A * (T/T_ref)^n * exp(-Ea/RT)"
        self.stoichiometry_by_name = {"reactants": {}, "products": {}}
        self.stoich_labels = {}
        self.update_position()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:
            if self.scene():
                QTimer.singleShot(0, self.update_stoichiometry_display)
        return super().itemChange(change, value)

    def get_unique_species(self, role):
        node = self.start_item if role == 'reactants' else self.end_item
        if not node: return set()
        
        species_set = set()
        if isinstance(node, SpeciesItem):
            species_set.add(node)
        elif isinstance(node, GroupItem):
            for item in node.contained_items:
                species_set.add(item)
        return species_set

    def update_stoichiometry_display(self):
        if not self.scene(): return

        for label in self.stoich_labels.values():
            if label.scene() == self.scene():
                self.scene().removeItem(label)
        self.stoich_labels.clear()

        for role in ['reactants', 'products']:
            for s_item in self.get_unique_species(role):
                label = StoichiometryItem(self, s_item, parent=self)
                self.stoich_labels[s_item] = label
        
        self.update_label_positions()

    def update_label_positions(self):
        for s_item, label in self.stoich_labels.items():
            species_rect = s_item.sceneBoundingRect()
            label_rect = label.boundingRect()
            label.setPos(
                species_rect.left() - label_rect.width() - 4, 
                species_rect.center().y() - label_rect.height() / 2
            )

    def update_stoichiometry_from_canvas(self, species_item, new_factor):
        role = self.stoich_labels[species_item].get_role()
        s_name = species_item.toPlainText()
        
        if role not in self.stoichiometry_by_name: self.stoichiometry_by_name[role] = {}
        self.stoichiometry_by_name[role][s_name] = new_factor
        
        if self.isSelected() and self.scene() and hasattr(self.scene(), 'properties_panel'):
             self.scene().properties_panel.show_properties(self)

    def update_stoichiometry_from_panel(self, role, species_name, new_factor):
        if role not in self.stoichiometry_by_name: self.stoichiometry_by_name[role] = {}
        self.stoichiometry_by_name[role][species_name] = new_factor
        
        for s_item, label in self.stoich_labels.items():
            if s_item.toPlainText() == species_name:
                label.setPlainText(str(new_factor))
                label.setVisible(new_factor > 1)
                break

    def to_dict(self): 
        return {key: getattr(self, key) for key in ['rate_constant', 'arrow_type', 'reaction_string', 'reaction_order', 'temperature_min', 'temperature_max', 'pressure', 'arrhenius_A', 'temperature_exponent_n', 'activation_energy_Ea', 'rate_expression']}

    def set_rate_constant(self, text): self.rate_constant = text; self.label.setPlainText(text); self.update_position()
    def set_arrow_type(self, arrow_type): self.arrow_type = arrow_type; self.update_position()
    def update_position(self):
        if not self.start_item or not self.end_item: return
        start_center, end_center = self.start_item.sceneBoundingRect().center(), self.end_item.sceneBoundingRect().center()
        line = QLineF(start_center, end_center); p1 = self._get_intersection_point(self.start_item, line); p2 = self._get_intersection_point(self.end_item, QLineF(line.p2(), line.p1()))
        path = QPainterPath(p1); path.lineTo(p2)
        if self.arrow_type == "Forward": self._draw_arrowhead(path, QLineF(p1, p2))
        elif self.arrow_type == "Backward": self._draw_arrowhead(path, QLineF(p2, p1))
        elif self.arrow_type == "Equilibrium": self._draw_equilibrium_heads(path, p1, p2)
        self.setPath(path); self._update_label_position()
        self.update_label_positions()

    def _update_label_position(self):
        line = QLineF(self.start_item.sceneBoundingRect().center(), self.end_item.sceneBoundingRect().center())
        center_point, angle = line.center(), line.angle()
        if 90 < angle < 270: angle += 180; offset_y = 15 
        else: offset_y = -15 
        transform = QTransform().translate(center_point.x(), center_point.y()).rotate(-line.angle()).translate(0, offset_y)
        label_rect = self.label.boundingRect(); final_pos = transform.map(QPointF(-label_rect.width() / 2, -label_rect.height() / 2))
        self.label.setPos(final_pos); self.label.setRotation(-line.angle())
    def _get_intersection_point(self, item, line):
        item_rect = item.sceneBoundingRect()
        sides = [QLineF(item_rect.topLeft(), item_rect.topRight()), QLineF(item_rect.topRight(), item_rect.bottomRight()), QLineF(item_rect.bottomRight(), item_rect.bottomLeft()), QLineF(item_rect.bottomLeft(), item_rect.topLeft())]
        for side in sides:
            intersect_type, intersect_point = line.intersects(side)
            if intersect_type == QLineF.IntersectionType.BoundedIntersection: return intersect_point
        return item.sceneBoundingRect().center()
    def _draw_arrowhead(self, path, line):
        if line.length() == 0: return
        angle = line.angle(); p1 = line.p2() + QLineF.fromPolar(12.0, angle + 180 - 25).p2(); p2 = line.p2() + QLineF.fromPolar(12.0, angle + 180 + 25).p2()
        path.moveTo(line.p2()); path.lineTo(p1); path.moveTo(line.p2()); path.lineTo(p2)
    def _draw_equilibrium_heads(self, path, p1, p2):
        line = QLineF(p1, p2);
        if line.length() < 20: return
        top_line = QLineF(p1, p2); top_line.setLength(top_line.length() - 5); angle = top_line.angle(); barb = top_line.p2() + QLineF.fromPolar(12.0, angle + 180 - 25).p2(); path.moveTo(top_line.p2()); path.lineTo(barb)
        bottom_line = QLineF(p2, p1); bottom_line.setLength(bottom_line.length() - 5); angle = bottom_line.angle(); barb = bottom_line.p2() + QLineF.fromPolar(12.0, angle + 180 + 25).p2(); path.moveTo(bottom_line.p2()); path.lineTo(barb)
    def detach(self): self.start_item.remove_arrow(self); self.end_item.remove_arrow(self)


class GroupItem(QGraphicsItem):
    def __init__(self, items, title, parent=None):
        super().__init__(parent); self.contained_items, self.title, self.arrows = items, title, []
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable); self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges); self.setZValue(-1); self.recalculate_bounds()
    def recalculate_bounds(self):
        if not self.contained_items: self._bounds = QRectF(); return
        rect = self.contained_items[0].sceneBoundingRect()
        for item in self.contained_items[1:]: rect = rect.united(item.sceneBoundingRect())
        self._bounds = self.mapFromScene(rect).boundingRect().adjusted(-20, -20, 20, 20); self.prepareGeometryChange()
    def boundingRect(self): return self._bounds
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing); pen = QPen(QColor("#007bff"), 2, Qt.PenStyle.DashLine)
        if self.isSelected(): pen.setColor(QColor("#ffc107")); pen.setWidth(3)
        painter.setPen(pen); painter.setBrush(QBrush(QColor(0, 123, 255, 15))); painter.drawRoundedRect(self.boundingRect(), 10, 10)
        font = QFont("Arial", 10, QFont.Weight.Bold); painter.setFont(font); painter.setPen(QColor("#0056b3"))
        text_rect = self.boundingRect().adjusted(10, 5, -10, -5)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.title)
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            old_pos = self.pos(); dx, dy = value.x() - old_pos.x(), value.y() - old_pos.y()
            if dx != 0 or dy != 0:
                for item in self.contained_items: item.moveBy(dx, dy)
                for arrow in self.arrows: arrow.update_position()
        return super().itemChange(change, value)
    def add_arrow(self, arrow): self.arrows.append(arrow)
    def remove_arrow(self, arrow):
        if arrow in self.arrows: self.arrows.remove(arrow)
    def detach(self): pass

class PropertiesPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.form_layout = QFormLayout()
        self.setLayout(self.form_layout)
        self.current_item = None
        self._is_updating = False
        self.widgets = {}
        self.last_edited_attr = None
        self.show_welcome_message()

    def show_properties(self, item):
        self._is_updating = True
        self.clear_layout()
        self.current_item = item
        if isinstance(item, SpeciesItem):
            self.show_species_properties(item)
        elif isinstance(item, ArrowItem):
            self.show_arrow_properties(item)
        elif isinstance(item, GroupItem):
            self.form_layout.addRow(QLabel(f"<h3>Gruppe: {item.title}</h3>"))
        self._is_updating = False

    def show_arrow_properties(self, item):
        item.update_stoichiometry_display()
        self.form_layout.addRow(QLabel("<h3>Reaktionseigenschaften</h3>"))
        groups = {"Allgemein": [("Label (k)", "rate_constant"), ("Reaktionsordnung", "reaction_order"), ("Reaktionsgleichung", "reaction_string")], "Bedingungen": [("Min. Temperatur (K)", "temperature_min"), ("Max. Temperatur (K)", "temperature_max"), ("Druck (Pa)", "pressure")], "Geschwindigkeitsgesetz": [("Arrhenius-Faktor (A)", "arrhenius_A"), ("Temp.-Exponent (n)", "temperature_exponent_n"), ("Aktivierungsenergie (Ea, J/mol)", "activation_energy_Ea"), ("Ausdruck", "rate_expression")]}
        for group_name, props in groups.items():
            self.form_layout.addRow(QLabel(f"<b>{group_name}</b>"))
            for label, attr in props:
                widget = QLineEdit(str(getattr(item, attr)))
                widget.textChanged.connect(lambda text, a=attr: self.update_property(a, text))
                self.form_layout.addRow(label + ":", widget)
        combo = QComboBox(); combo.addItems(["Forward", "Backward", "Equilibrium"]); combo.setCurrentText(item.arrow_type); combo.currentTextChanged.connect(item.set_arrow_type); self.form_layout.addRow("Pfeiltyp:", combo)
        self.form_layout.addRow(QLabel("<b>Stöchiometrie</b>"))
        self._add_stoichiometry_widgets(item, 'reactants')
        self._add_stoichiometry_widgets(item, 'products')

    def _add_stoichiometry_widgets(self, arrow_item, role):
        species_in_node = arrow_item.get_unique_species(role)
        if not species_in_node: return
        for s_item in sorted(species_in_node, key=lambda s: s.toPlainText()):
            name = s_item.toPlainText()
            current_stoich = arrow_item.stoichiometry_by_name.get(role, {}).get(name, 1)
            widget = QLineEdit(str(current_stoich))
            widget.textChanged.connect(lambda text, r=role, n=name: self._update_stoichiometry(r, n, text))
            role_label = "Edukt" if role == 'reactants' else "Produkt"
            self.form_layout.addRow(f"{role_label}: {name}", widget)

    def _update_stoichiometry(self, role, name, text):
        if not self.current_item or not isinstance(self.current_item, ArrowItem): return
        try:
            val = int(text)
            if val > 0:
                self.current_item.update_stoichiometry_from_panel(role, name, val)
        except (ValueError, TypeError):
            pass

    def show_species_properties(self, item):
        self.widgets.clear()
        
        groups = {
            "Grundlagen": [("Name", "name"), ("Summenformel", "formula"), ("SMILES", "smiles")],
            "Stoffmenge & Masse": [("Masse (g)", "mass"), ("Stoffmenge (mol)", "moles"), ("Molare Masse (g/mol)", "molar_mass")],
            "Kinetik & Startwerte": [("Startkonzentration (mol/L)", "start_concentration"), ("Akt. Konzentration (mol/L)", "concentration")],
            "Thermodynamik": [("ΔHf (kJ/mol)", "delta_hf"), ("S0 (J/mol*K)", "s0"), ("ΔGf (kJ/mol)", "gibbs_g0")],
        }

        for group_name, props in groups.items():
            self.form_layout.addRow(QLabel(f"<b>{group_name}</b>"))
            for label, attr in props:
                value_str = item.toPlainText() if attr == "name" else str(getattr(item, attr))
                widget = QLineEdit(value_str)
                widget.textChanged.connect(lambda text, a=attr: self._on_widget_changed(a))
                self.form_layout.addRow(label + ":", widget)
                self.widgets[attr] = widget
        
        self.last_edited_attr = None
        self.perform_update() 

    def _on_widget_changed(self, attr):
        if not self._is_updating:
            self.last_edited_attr = attr
        self.perform_update()

    def perform_update(self):
        if self._is_updating or not isinstance(self.current_item, SpeciesItem):
            return
        
        self._is_updating = True

        def text_to_float(text_str):
            try: return float(text_str)
            except (ValueError, TypeError): return None

        values = {attr: text_to_float(widget.text()) for attr, widget in self.widgets.items() if attr not in ['name', 'formula', 'smiles']}
        for attr in ['name', 'formula', 'smiles']:
            if attr in self.widgets: values[attr] = self.widgets[attr].text()

        m, n, mm = values.get('mass'), values.get('moles'), values.get('molar_mass')
        c = values.get('concentration')
        dh, ds = values.get('delta_hf'), values.get('s0')
        vol = text_to_float(self.main_window.sim_volume_edit.text())
        temp = text_to_float(self.main_window.sim_temp_edit.text())
        last_edit = self.last_edited_attr

        if last_edit in ['moles', 'molar_mass'] and n is not None and mm is not None: values['mass'] = n * mm
        elif last_edit == 'mass' and m is not None and mm is not None and mm > 0: values['moles'] = m / mm
        elif last_edit in ['mass', 'moles'] and m is not None and n is not None and n > 0: values['molar_mass'] = m / n

        if vol is not None and vol > 0:
            if last_edit in ['moles', 'volume'] and values.get('moles') is not None: values['concentration'] = values['moles'] / vol
            elif last_edit in ['concentration', 'volume'] and c is not None: values['moles'] = c * vol
        
        if last_edit in ['delta_hf', 's0', 'temperature'] and dh is not None and ds is not None and temp is not None and temp > 0:
            values['gibbs_g0'] = dh - temp * (ds / 1000.0)

        for attr, value in values.items():
            if attr in ['name', 'formula', 'smiles']:
                if attr == 'name': self.current_item.setPlainText(value)
                else: setattr(self.current_item, attr, value)
            else:
                setattr(self.current_item, attr, value if value is not None else 0.0)

        for attr, widget in self.widgets.items():
            if attr in ['name', 'formula', 'smiles']: continue
            
            value = values.get(attr)
            new_val_str = f"{value:.4g}" if value is not None else ""
            
            if widget.text() != new_val_str:
                widget.setText(new_val_str)

        self._is_updating = False

    def update_property(self, attr, value):
        if not self.current_item: return
        try:
            if isinstance(value, bool): setattr(self.current_item, attr, value)
            elif attr == "name": 
                old_name = self.current_item.toPlainText()
                new_name = value
                self.current_item.setPlainText(new_name)
                for arrow in self.current_item.arrows:
                    for role_data in arrow.stoichiometry_by_name.values():
                        if old_name in role_data:
                            role_data[new_name] = role_data.pop(old_name)
                    if arrow.isSelected():
                        self.show_arrow_properties(arrow)
            elif hasattr(self.current_item, attr) and isinstance(getattr(self.current_item, attr), (int, float)): setattr(self.current_item, attr, float(value))
            else: setattr(self.current_item, attr, value)
            if attr == "rate_constant": self.current_item.label.setPlainText(value)
        except (ValueError, TypeError, AttributeError): pass
    def clear_layout(self):
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
    def show_welcome_message(self): self.clear_layout(); welcome = QLabel("Kein Element ausgewählt."); welcome.setAlignment(Qt.AlignmentFlag.AlignCenter); self.form_layout.addRow(welcome)

class GraphicsScene(QGraphicsScene):
    def __init__(self, mode_provider, undo_stack, status_bar_notifier):
        super().__init__(); self.mode_provider, self.undo_stack, self.status_bar_notifier = mode_provider, undo_stack, status_bar_notifier; self.arrow_start_item, self.rubber_band_line = None, None
        self.properties_panel = None
    
    def update_from_analysis(self, analysis_data):
        arrows = [item for item in self.items() if isinstance(item, ArrowItem)]
        for rate_label, data in analysis_data.items():
            for arrow in arrows:
                if arrow.rate_constant == rate_label:
                    order_str = data['best_fit_order']; arrow.reaction_order = "0" if "zero" in order_str else "1" if "first" in order_str else "2"
                    arrow.arrhenius_A = data['calculated_k']; arrow.activation_energy_Ea = 0; break
    
    def serialize(self):
        all_species = [i for i in self.items() if isinstance(i, SpeciesItem)]
        arrows = [i for i in self.items() if isinstance(i, ArrowItem)]
        groups = [i for i in self.items() if isinstance(i, GroupItem)]

        s_map_obj_to_idx = {item: i for i, item in enumerate(all_species)}
        g_map_obj_to_id = {item: f"group_{i}" for i, item in enumerate(groups)}
        node_map = s_map_obj_to_idx | g_map_obj_to_id
        
        s_map_name_to_idx = {item.toPlainText(): i for item, i in s_map_obj_to_idx.items()}

        species_data = [item.to_dict() for item in all_species]
        group_data = [{'id': g_map_obj_to_id[g], 'title': g.title, 'items': [s_map_obj_to_idx[s] for s in g.contained_items if s in s_map_obj_to_idx]} for g in groups]
        
        arrow_data = []
        for arrow in arrows:
            base_data = arrow.to_dict()
            base_data['start_id'] = node_map.get(arrow.start_item)
            base_data['end_id'] = node_map.get(arrow.end_item)
            
            stoich_by_idx = {"reactants": {}, "products": {}}
            for role in ["reactants", "products"]:
                for name, factor in arrow.stoichiometry_by_name.get(role, {}).items():
                    if name in s_map_name_to_idx:
                        idx = s_map_name_to_idx[name]
                        stoich_by_idx[role][str(idx)] = factor
            base_data['stoichiometry'] = stoich_by_idx
            arrow_data.append(base_data)

        return {'species': species_data, 'groups': group_data, 'arrows': arrow_data}

    def deserialize(self, data):
        self.clear(); self.undo_stack.clear()
        if 'species' not in data: return
        
        species_items = [SpeciesItem.from_dict(sd) for sd in data.get('species', [])]
        for item in species_items: self.addItem(item)
        
        s_map_idx_to_obj = {i: item for i, item in enumerate(species_items)}
        s_map_idx_to_name = {i: item.toPlainText() for i, item in enumerate(species_items)}

        group_items = {}
        if 'groups' in data:
            for group_data in data.get('groups', []):
                contained = [s_map_idx_to_obj[i] for i in group_data['items'] if i in s_map_idx_to_obj]
                group = GroupItem(contained, group_data['title']); group_items[group_data['id']] = group; self.addItem(group)
        
        node_map = s_map_idx_to_obj | group_items
        
        if 'arrows' in data:
            for arrow_data in data.get('arrows', []):
                start_node, end_node = node_map.get(arrow_data.get('start_id')), node_map.get(arrow_data.get('end_id'))
                if start_node and end_node:
                    arrow = ArrowItem(start_node, end_node, arrow_data.get('rate_constant', 'k'))
                    for key, value in arrow_data.items():
                        if hasattr(arrow, key): setattr(arrow, key, value)
                    arrow.set_arrow_type(arrow_data.get('arrow_type', 'Forward'))
                    
                    stoich_by_name = {"reactants": {}, "products": {}}
                    for role in ["reactants", "products"]:
                        for idx_str, factor in arrow_data.get('stoichiometry', {}).get(role, {}).items():
                            idx = int(idx_str)
                            if idx in s_map_idx_to_name:
                                name = s_map_idx_to_name[idx]
                                stoich_by_name[role][name] = factor
                    arrow.stoichiometry_by_name = stoich_by_name
                    self.addItem(arrow)

    def mousePressEvent(self, event):
        mode = self.mode_provider()
        if mode == 'ADD_SPECIES': cmd = AddCommand(SpeciesItem("Spezies", event.scenePos()), self, "Spezies hinzugefügt"); self.undo_stack.push(cmd)
        elif mode == 'ADD_ARROW': self.handle_arrow_drawing(event)
        else: super().mousePressEvent(event)
    def handle_arrow_drawing(self, event):
        target_item = next((item for item in self.items(event.scenePos()) if isinstance(item, (SpeciesItem, GroupItem))), None)
        if not self.arrow_start_item:
            if target_item:
                self.arrow_start_item = target_item
                if isinstance(target_item, SpeciesItem): target_item.update_visual_state(arrow_start=True)
                start_pos = target_item.sceneBoundingRect().center()
                self.rubber_band_line = self.addLine(QLineF(start_pos, event.scenePos()), QPen(QColor("#333"), 2, Qt.PenStyle.DashLine))
                self.status_bar_notifier("Wählen Sie das Ziel aus (Esc zum Abbrechen).")
        else:
            if target_item and self.arrow_start_item != target_item:
                cmd = AddCommand(ArrowItem(self.arrow_start_item, target_item, self.get_next_k_value()), self, "Pfeil hinzugefügt"); self.undo_stack.push(cmd)
            self.cancel_arrow_drawing()
    def get_next_k_value(self):
        max_k = 0;
        for item in self.items():
            if isinstance(item, ArrowItem):
                rate = item.rate_constant
                if rate.startswith('k') and rate[1:].isdigit(): max_k = max(max_k, int(rate[1:]))
        return f"k{max_k + 1}"
    def mouseMoveEvent(self, event):
        if self.rubber_band_line: self.rubber_band_line.setLine(QLineF(self.arrow_start_item.sceneBoundingRect().center(), event.scenePos()))
        else: super().mouseMoveEvent(event)
    def cancel_arrow_drawing(self):
        if self.arrow_start_item and isinstance(self.arrow_start_item, SpeciesItem): self.arrow_start_item.update_visual_state()
        if self.rubber_band_line: self.removeItem(self.rubber_band_line)
        self.arrow_start_item, self.rubber_band_line = None, None; self.status_bar_notifier("Bereit.")
    def delete_selected_items(self):
        items = self.selectedItems()
        if not items: return
        all_items_to_delete = set()
        for item in items:
            all_items_to_delete.add(item)
            if isinstance(item, (SpeciesItem, GroupItem)): 
                all_items_to_delete.update(item.arrows)
            if isinstance(item, StoichiometryItem):
                all_items_to_delete.add(item.arrow)
        
        cmd = DeleteCommand(list(all_items_to_delete), self, "Elemente gelöscht"); self.undo_stack.push(cmd)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Kinetics Canvas"); self.setGeometry(100, 100, 1400, 900)
        self.current_mode, self.undo_stack = 'SELECT', QUndoStack(self)
        self.scene = GraphicsScene(lambda: self.current_mode, self.undo_stack, self.statusBar().showMessage)
        self.scene.setSceneRect(0, 0, 2000, 2000); self.scene.setBackgroundBrush(QColor("#fafafa"))
        self.view = QGraphicsView(self.scene); self.view.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing); self.setCentralWidget(self.view)
        
        self.plot_dir = tempfile.mkdtemp(prefix="kinetics_plots_")
        
        self.create_actions(); self.create_menus(); self.create_toolbars(); self.create_properties_dock()
        self.scene.selectionChanged.connect(self.on_selection_changed); self.statusBar().showMessage("Bereit."); self.set_mode(self.current_mode)
        self.scene.properties_panel = self.properties_panel

    def create_actions(self):
        self.open_action = QAction(QIcon.fromTheme('document-open'), "Öffnen (.kin)...", self); self.open_action.setShortcut(QKeySequence.StandardKey.Open); self.open_action.triggered.connect(self.handle_open)
        self.save_action = QAction(QIcon.fromTheme('document-save'), "Speichern (.kin)...", self); self.save_action.setShortcut(QKeySequence.StandardKey.Save); self.save_action.triggered.connect(self.handle_save)
        self.export_png_action = QAction(QIcon.fromTheme('image-x-generic'), "Exportieren als PNG...", self); self.export_png_action.triggered.connect(self.handle_export_png)
        self.undo_action = self.undo_stack.createUndoAction(self, "Rückgängig"); self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.redo_action = self.undo_stack.createRedoAction(self, "Wiederherstellen"); self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.delete_action = QAction("Löschen", self); self.delete_action.setShortcut(QKeySequence.StandardKey.Delete); self.delete_action.triggered.connect(self.scene.delete_selected_items); self.addAction(self.delete_action)
        self.create_group_action = QAction(QIcon.fromTheme('object-group'), "Gruppe erstellen", self); self.create_group_action.triggered.connect(self.handle_create_group)
        self.start_simulation_action = QAction(QIcon.fromTheme('media-playback-start'), "Simulation starten", self); self.start_simulation_action.triggered.connect(self.handle_start_simulation)
    def create_menus(self):
        file_menu = self.menuBar().addMenu("&Datei"); file_menu.addAction(self.open_action); file_menu.addAction(self.save_action); file_menu.addSeparator(); file_menu.addAction(self.export_png_action)
        edit_menu = self.menuBar().addMenu("&Bearbeiten"); edit_menu.addAction(self.undo_action); edit_menu.addAction(self.redo_action); edit_menu.addSeparator(); edit_menu.addAction(self.delete_action); edit_menu.addSeparator(); edit_menu.addAction(self.create_group_action)
        sim_menu = self.menuBar().addMenu("&Simulation"); sim_menu.addAction(self.start_simulation_action)
    def create_toolbars(self):
        main_toolbar = QToolBar("Hauptwerkzeuge"); self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, main_toolbar)
        self.action_group = QActionGroup(self); self.action_group.setExclusive(True)
        actions_data = [("edit-select", "Auswählen", 'SELECT'), ("list-add", "Spezies", 'ADD_SPECIES'), ("draw-arrow", "Pfeil", 'ADD_ARROW')]
        for icon, text, mode in actions_data:
            action = QAction(QIcon.fromTheme(icon), text, self); action.setCheckable(True)
            action.setData(mode); action.triggered.connect(self.toolbar_action_triggered); main_toolbar.addAction(action); self.action_group.addAction(action)
        self.action_group.actions()[0].setChecked(True); main_toolbar.addSeparator(); main_toolbar.addAction(self.create_group_action)
        
        sim_toolbar = QToolBar("Simulation"); self.addToolBar(Qt.ToolBarArea.TopToolBarArea, sim_toolbar)
        sim_toolbar.addWidget(QLabel(" Dauer (s): ")); self.sim_time_edit = QLineEdit("30.0"); self.sim_time_edit.setFixedWidth(50); sim_toolbar.addWidget(self.sim_time_edit)
        sim_toolbar.addWidget(QLabel(" Temp. (K): ")); self.sim_temp_edit = QLineEdit("298.15"); self.sim_temp_edit.setFixedWidth(60); sim_toolbar.addWidget(self.sim_temp_edit)
        sim_toolbar.addWidget(QLabel(" Volumen (L): ")); self.sim_volume_edit = QLineEdit("1.0"); self.sim_volume_edit.setFixedWidth(50); sim_toolbar.addWidget(self.sim_volume_edit)
        sim_toolbar.addAction(self.start_simulation_action)

        self.sim_temp_edit.textChanged.connect(lambda: self.properties_panel._on_widget_changed('temperature'))
        self.sim_volume_edit.textChanged.connect(lambda: self.properties_panel._on_widget_changed('volume'))

    def create_properties_dock(self):
        dock = QDockWidget("Eigenschaften")
        self.properties_panel = PropertiesPanel(self)
        dock.setWidget(self.properties_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        
    def handle_start_simulation(self):
        try: 
            sim_time = float(self.sim_time_edit.text())
            temp_k = float(self.sim_temp_edit.text())
        except ValueError: 
            QMessageBox.critical(self, "Fehler", "Ungültige Eingabe für Simulationsparameter."); return
            
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".kin", encoding='utf-8') as tmp_file:
            json.dump(self.scene.serialize(), tmp_file, indent=4); self.temp_kin_path = tmp_file.name
            
        self.statusBar().showMessage("Simulation läuft..."); self.start_simulation_action.setEnabled(False)
        self.sim_thread = SimulationThread(self.temp_kin_path, sim_time, temp_k, self.plot_dir)
        self.sim_thread.finished.connect(self.on_simulation_finished); self.sim_thread.error.connect(self.on_simulation_error); self.sim_thread.start()

    def on_simulation_finished(self, results):
        self.statusBar().showMessage("Simulation erfolgreich!", 5000); self.start_simulation_action.setEnabled(True)
        if "analysis" in results: self.scene.update_from_analysis(results["analysis"])
        self.plot_dialog = PlotDialog(results, self); self.plot_dialog.show()
        
    def on_simulation_error(self, message):
        self.statusBar().showMessage("Simulation fehlgeschlagen.", 5000); self.start_simulation_action.setEnabled(True)
        QMessageBox.critical(self, "Simulationsfehler", message)
        
    def handle_create_group(self):
        selected = [item for item in self.scene.selectedItems() if isinstance(item, SpeciesItem)]
        if len(selected) < 1: self.statusBar().showMessage("Bitte mind. eine Spezies auswählen.", 3000); return
        title, ok = QInputDialog.getText(self, "Gruppe erstellen", "Name:", text="Edukte")
        if ok and title: 
            cmd = AddCommand(GroupItem(selected, title), self.scene, "Gruppe hinzugefügt")
            self.undo_stack.push(cmd)
            for item in selected:
                for arrow in item.arrows:
                    arrow.update_stoichiometry_display()

    def handle_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Szene öffnen", "", "Kinetics Files (*.kin)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f: data = json.load(f)
                self.scene.deserialize(data); self.statusBar().showMessage(f"Szene geladen von {path}", 5000)
            except Exception as e: QMessageBox.critical(self, "Fehler beim Laden", str(e)); self.statusBar().showMessage(f"Fehler beim Laden: {e}", 5000)

    def handle_save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Szene speichern", "", "Kinetics Files (*.kin)")
        if path:
            if isinstance(self.properties_panel.current_item, SpeciesItem):
                self.properties_panel.perform_update()
            with open(path, 'w', encoding='utf-8') as f: json.dump(self.scene.serialize(), f, indent=4)
            self.statusBar().showMessage(f"Szene gespeichert in {path}", 5000)

    def handle_export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Als PNG exportieren", "", "PNG Images (*.png)")
        if path:
            for item in self.scene.selectedItems(): item.setSelected(False)
            rect = self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20)
            image = QImage(rect.size().toSize(), QImage.Format.Format_ARGB32); image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.scene.render(painter, QRectF(image.rect()), rect); painter.end()
            if image.save(path): self.statusBar().showMessage(f"Exportiert als {path}", 5000)
            else: self.statusBar().showMessage("Fehler beim Exportieren", 5000)

    def toolbar_action_triggered(self): self.set_mode(self.sender().data())

    def set_mode(self, mode):
        if self.current_mode != mode: self.scene.cancel_arrow_drawing()
        self.current_mode = mode
        if mode == 'SELECT': self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else: self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        for action in self.action_group.actions():
            if action.data() == mode: action.setChecked(True)
        self.statusBar().showMessage(f"Modus: {mode}")

    def on_selection_changed(self):
        if sip.isdeleted(self.scene) or (hasattr(self, 'properties_panel') and sip.isdeleted(self.properties_panel)):
            return
            
        items = self.scene.selectedItems()
        if len(items) == 1:
            self.properties_panel.show_properties(items[0])
        else:
            self.properties_panel.show_welcome_message()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())