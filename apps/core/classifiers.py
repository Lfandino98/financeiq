"""
Motor de clasificación inteligente de gastos.
Sistema híbrido: reglas por palabras clave + fallback.
Preparado para integración futura con ML/IA.
"""
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


# ============================================================
# BASE DE CONOCIMIENTO: PALABRAS CLAVE POR CATEGORÍA
# ============================================================

KEYWORD_RULES = {
    'transporte': {
        'keywords': [
            'uber', 'didi', 'taxi', 'cabify', 'lyft', 'bus', 'metro',
            'tren', 'gasolina', 'combustible', 'peaje', 'parking',
            'estacionamiento', 'bicicleta', 'moto', 'avion', 'vuelo',
            'aerolinea', 'boleto', 'pasaje', 'transmilenio', 'sitp',
            'autopista', 'toll', 'nafta', 'diesel', 'gasolinera',
        ],
        'patterns': [r'uber\s*\w*', r'taxi\s*\w*', r'gas(olina|olinera)?'],
        'priority': 1,
    },
    'comida': {
        'keywords': [
            'pizza', 'hamburguesa', 'burger', 'restaurante', 'restaurant',
            'cafe', 'cafeteria', 'almuerzo', 'desayuno', 'cena', 'comida',
            'sushi', 'tacos', 'empanadas', 'pollo', 'dominos', 'mcdonalds',
            'kfc', 'subway', 'rappi', 'ifood', 'uber eats', 'pedidosya',
            'mercado', 'supermercado', 'grocery', 'carulla', 'exito',
            'jumbo', 'walmart', 'lidl', 'aldi', 'panaderia', 'pasteleria',
            'heladeria', 'bar', 'cerveza', 'vino', 'bebida', 'snack',
        ],
        'patterns': [r'super\s*mercado', r'uber\s*eats', r'rappi\s*\w*'],
        'priority': 2,
    },
    'entretenimiento': {
        'keywords': [
            'netflix', 'spotify', 'disney', 'hbo', 'amazon prime', 'youtube',
            'cine', 'cinema', 'teatro', 'concierto', 'evento', 'fiesta',
            'juego', 'videojuego', 'steam', 'playstation', 'xbox', 'nintendo',
            'twitch', 'apple tv', 'paramount', 'crunchyroll', 'deezer',
            'discoteca', 'club', 'bar', 'karaoke', 'bowling', 'escape room',
        ],
        'patterns': [r'netflix\s*\w*', r'spotify\s*\w*', r'disney\s*\+?'],
        'priority': 3,
    },
    'salud': {
        'keywords': [
            'farmacia', 'medicamento', 'medicina', 'doctor', 'medico',
            'hospital', 'clinica', 'consulta', 'cita medica', 'dentista',
            'odontologo', 'psicologo', 'terapia', 'gym', 'gimnasio',
            'crossfit', 'yoga', 'pilates', 'vitaminas', 'suplemento',
            'laboratorio', 'examen', 'radiografia', 'seguro medico',
            'eps', 'prepagada', 'drogueria', 'botica',
        ],
        'patterns': [r'dr\.?\s*\w+', r'dra\.?\s*\w+', r'clinica\s*\w*'],
        'priority': 4,
    },
    'educacion': {
        'keywords': [
            'universidad', 'colegio', 'escuela', 'curso', 'taller',
            'libro', 'libreria', 'udemy', 'coursera', 'platzi', 'linkedin',
            'matricula', 'pension', 'mensualidad', 'tutoria', 'clase',
            'seminario', 'diplomado', 'maestria', 'doctorado', 'certificado',
            'material', 'cuaderno', 'lapiz', 'papeleria',
        ],
        'patterns': [r'udemy\s*\w*', r'coursera\s*\w*', r'platzi\s*\w*'],
        'priority': 5,
    },
    'hogar': {
        'keywords': [
            'arriendo', 'alquiler', 'renta', 'hipoteca', 'servicios',
            'agua', 'luz', 'electricidad', 'gas', 'internet', 'telefono',
            'celular', 'cable', 'administracion', 'condominio', 'mueble',
            'electrodomestico', 'nevera', 'lavadora', 'reparacion',
            'plomero', 'electricista', 'pintura', 'limpieza', 'aseo',
        ],
        'patterns': [r'arriendo\s*\w*', r'servicios?\s*p[uú]blicos?'],
        'priority': 6,
    },
    'ropa': {
        'keywords': [
            'ropa', 'zapatos', 'zapatillas', 'tenis', 'camisa', 'pantalon',
            'vestido', 'falda', 'chaqueta', 'abrigo', 'zara', 'h&m',
            'forever21', 'nike', 'adidas', 'puma', 'reebok', 'mango',
            'pull&bear', 'bershka', 'stradivarius', 'accesorios', 'bolso',
            'cartera', 'cinturon', 'gorra', 'sombrero',
        ],
        'patterns': [r'zara\s*\w*', r'h&m\s*\w*'],
        'priority': 7,
    },
    'tecnologia': {
        'keywords': [
            'celular', 'computador', 'laptop', 'tablet', 'iphone', 'samsung',
            'apple', 'huawei', 'xiaomi', 'auriculares', 'audifonos', 'mouse',
            'teclado', 'monitor', 'impresora', 'camara', 'software',
            'aplicacion', 'app', 'dominio', 'hosting', 'servidor',
            'amazon aws', 'google cloud', 'microsoft',
        ],
        'patterns': [r'apple\s*\w*', r'samsung\s*\w*', r'iphone\s*\d*'],
        'priority': 8,
    },
    'viajes': {
        'keywords': [
            'hotel', 'hostal', 'airbnb', 'booking', 'viaje', 'vacaciones',
            'turismo', 'tour', 'excursion', 'crucero', 'resort', 'spa',
            'maleta', 'equipaje', 'visa', 'pasaporte',
        ],
        'patterns': [r'airbnb\s*\w*', r'booking\s*\w*'],
        'priority': 9,
    },
    'finanzas': {
        'keywords': [
            'banco', 'transferencia', 'comision', 'cuota', 'prestamo',
            'credito', 'deuda', 'inversion', 'accion', 'bono', 'fondo',
            'seguro', 'pension', 'ahorro', 'plazo fijo', 'cdt',
            'tarjeta', 'interes', 'dividendo',
        ],
        'patterns': [r'banco\s*\w*', r'tarjeta\s*\w*'],
        'priority': 10,
    },
}


class ExpenseClassifier:
    """
    Clasificador inteligente de gastos basado en reglas.
    
    Arquitectura:
    1. Normalización del texto
    2. Búsqueda exacta de palabras clave
    3. Búsqueda por patrones regex
    4. Scoring por relevancia
    5. Fallback a 'otros'
    
    Preparado para extensión con ML en el futuro.
    """

    def __init__(self):
        self.rules = KEYWORD_RULES
        self._build_index()

    def _build_index(self):
        """Construye índice invertido para búsqueda eficiente."""
        self.keyword_index = {}
        for category, config in self.rules.items():
            for keyword in config['keywords']:
                normalized = self._normalize(keyword)
                if normalized not in self.keyword_index:
                    self.keyword_index[normalized] = []
                self.keyword_index[normalized].append({
                    'category': category,
                    'priority': config['priority'],
                    'score': 1.0,
                })

    def _normalize(self, text: str) -> str:
        """Normaliza texto para comparación."""
        text = text.lower().strip()
        # Eliminar caracteres especiales pero mantener espacios
        text = re.sub(r'[^\w\s]', ' ', text)
        # Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        return text

    def _tokenize(self, text: str) -> list:
        """Divide el texto en tokens."""
        normalized = self._normalize(text)
        return normalized.split()

    def _score_by_keywords(self, text: str) -> dict:
        """Calcula score por palabras clave."""
        scores = {}
        normalized_text = self._normalize(text)
        tokens = self._tokenize(text)

        # Búsqueda de frases completas (mayor peso)
        for keyword, matches in self.keyword_index.items():
            if keyword in normalized_text:
                for match in matches:
                    cat = match['category']
                    # Frase completa tiene más peso que token individual
                    weight = 2.0 if ' ' in keyword else 1.0
                    scores[cat] = scores.get(cat, 0) + weight

        # Búsqueda por tokens individuales
        for token in tokens:
            if token in self.keyword_index:
                for match in self.keyword_index[token]:
                    cat = match['category']
                    scores[cat] = scores.get(cat, 0) + 0.5

        return scores

    def _score_by_patterns(self, text: str) -> dict:
        """Calcula score por patrones regex."""
        scores = {}
        normalized_text = self._normalize(text)

        for category, config in self.rules.items():
            for pattern in config.get('patterns', []):
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    scores[category] = scores.get(category, 0) + 1.5

        return scores

    def classify(self, description: str) -> dict:
        """
        Clasifica un gasto basado en su descripción.
        
        Returns:
            dict con:
                - category: nombre de la categoría
                - confidence: nivel de confianza (0-1)
                - method: método usado
                - alternatives: categorías alternativas
        """
        if not description or not description.strip():
            return self._fallback_result()

        try:
            # Paso 1: Score por palabras clave
            keyword_scores = self._score_by_keywords(description)

            # Paso 2: Score por patrones
            pattern_scores = self._score_by_patterns(description)

            # Paso 3: Combinar scores
            combined_scores = {}
            all_categories = set(
                list(keyword_scores.keys()) + list(pattern_scores.keys())
            )

            for cat in all_categories:
                kw_score = keyword_scores.get(cat, 0)
                pt_score = pattern_scores.get(cat, 0)
                # Los patrones tienen más peso
                combined_scores[cat] = kw_score + (pt_score * 1.5)

            if not combined_scores:
                return self._fallback_result()

            # Paso 4: Seleccionar mejor categoría
            best_category = max(combined_scores, key=combined_scores.get)
            best_score = combined_scores[best_category]
            total_score = sum(combined_scores.values())

            # Calcular confianza
            confidence = min(best_score / max(total_score, 1), 1.0)

            # Alternativas ordenadas
            alternatives = sorted(
                [
                    {'category': cat, 'score': score}
                    for cat, score in combined_scores.items()
                    if cat != best_category
                ],
                key=lambda x: x['score'],
                reverse=True
            )[:3]

            return {
                                'category': best_category,
                'confidence': round(confidence, 2),
                'method': 'keyword_pattern',
                'alternatives': alternatives,
                'raw_scores': combined_scores,
            }

        except Exception as e:
            logger.error(f"Error clasificando gasto '{description}': {e}")
            return self._fallback_result()

    def _fallback_result(self) -> dict:
        """Resultado por defecto cuando no hay clasificación."""
        return {
            'category': 'otros',
            'confidence': 0.0,
            'method': 'fallback',
            'alternatives': [],
            'raw_scores': {},
        }

    def suggest_categories(self, description: str) -> list:
        """
        Sugiere múltiples categorías posibles para una descripción.
        Útil para mostrar opciones al usuario.
        """
        result = self.classify(description)
        suggestions = [result['category']]

        for alt in result.get('alternatives', []):
            suggestions.append(alt['category'])

        return suggestions[:3]

    def batch_classify(self, descriptions: list) -> list:
        """Clasifica múltiples descripciones en lote."""
        return [
            {
                'description': desc,
                'classification': self.classify(desc)
            }
            for desc in descriptions
        ]


# Instancia global del clasificador (singleton)
expense_classifier = ExpenseClassifier()