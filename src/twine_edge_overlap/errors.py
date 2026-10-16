"""Actionable categories exposed by the CLI, without story contents."""

class ToolError(Exception):
    category='processamento'

class InputError(ToolError): category='entrada'
class FormatError(ToolError): category='formato'
class DependencyError(ToolError): category='dependência'
class EngineError(ToolError): category='motor'
class BudgetError(EngineError): category='limite'
class IntegrityError(ToolError): category='integridade'
class WriteError(ToolError): category='escrita'
