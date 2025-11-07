"""Definición de excepciones personalizadas para el proyecto."""


class DataValidationError(ValueError):
    """Se lanza cuando los datos no superan las validaciones definidas."""


class APIError(RuntimeError):
    """Errores provenientes de llamadas a APIs externas."""


class ConfigurationError(RuntimeError):
    """La configuración proporcionada es inválida o incompleta."""


class InsufficientDataError(RuntimeError):
    """No hay datos suficientes para completar la operación solicitada."""


