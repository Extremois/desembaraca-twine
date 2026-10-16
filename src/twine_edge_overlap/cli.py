"""Portuguese terminal interface for one local Twee file."""
import argparse
import sys
from .application import run
from .errors import ToolError,InputError


class Parser(argparse.ArgumentParser):
    def error(self,message): raise InputError('Informe exatamente um caminho .twee; consulte --help')


def main(argv=None):
    parser=Parser(prog='twine-edge-overlap',description='Reorganiza um arquivo Twee sem sobrescrever o original.')
    parser.add_argument('caminho',help='Caminho de um arquivo .twee com metadados de layout')
    parser.add_argument('--version',action='version',version='0.1.0.dev0')
    try:
        args=parser.parse_args(argv)
        result=run(args.caminho)
        print(f'Estado: {result.status}\n{result.reason}')
        print(f'Arquivo gerado: {result.path}')
        for label,a,b in zip(('Pares de arestas','Pares de nós','Pares aresta–nó'),result.before.values,result.after.values):
            print(f'{label}: {a} -> {b}')
        return 0 if result.status=='sucesso' else 2
    except KeyboardInterrupt:
        print('Falha: execução interrompida; nenhuma cópia parcial anunciada como válida.',file=sys.stderr)
        return 130
    except ToolError as exc:
        print(f'Falha ({exc.category}): {exc}',file=sys.stderr)
        return 1
    except (OSError,ValueError,TimeoutError,ArithmeticError) as exc:
        print(f'Falha de processamento: {type(exc).__name__}; nenhuma saída válida anunciada.',file=sys.stderr)
        return 1
    except Exception as exc:
        print(f'Falha inesperada de processamento ({type(exc).__name__}); nenhuma saída válida anunciada. Consulte a documentação ou relate o erro.',file=sys.stderr)
        return 1


if __name__=='__main__': sys.exit(main())
