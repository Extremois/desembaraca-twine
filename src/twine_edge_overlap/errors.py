"""Actionable categories exposed by the CLI, without story contents."""
import errno

class ToolError(Exception):
    category='processamento'

class InputError(ToolError): category='entrada'
class FormatError(ToolError): category='formato'
class DependencyError(ToolError): category='dependência'
class EngineError(ToolError): category='motor'
class BudgetError(EngineError): category='limite'
class IntegrityError(ToolError): category='integridade'
class WriteError(ToolError): category='escrita'


def execution_diagnostic(error, system):
    """Describe the observed execution failure, never guessed Gatekeeper/noexec causes."""
    if error.errno in (errno.EACCES, errno.EPERM):
        cause='O sistema negou a execução do componente'
        action='Verifique permissões e se a pasta permite executar programas'
    elif error.errno == errno.ENOEXEC:
        cause='O sistema não aceitou o formato do executável'
        action='Confira o sistema e a arquitetura nativos do Python e do pacote'
    elif error.errno == errno.ENOENT:
        cause='O executável ou um componente necessário à execução não foi encontrado'
        action='Obtenha novamente os componentes pelo projeto'
    else:
        cause='Não foi possível executar o componente de processamento'
        action='Confira as condições de execução do sistema'
    if system=='darwin':
        action+='; consulte a documentação para componentes assinados sob as proteções normais do macOS'
    return DependencyError(f'{cause}. Componente indisponível; nenhuma cópia gerada. {action} e repita --repair-runtime.')
