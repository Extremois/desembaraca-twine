"""Portuguese terminal interface for one local Twee file."""
import argparse
import sys
from .application import run
from .errors import ToolError,InputError
from .runtime import ensure_runtime


class Parser(argparse.ArgumentParser):
    def error(self,message): raise InputError('Informe exatamente um caminho .twee; consulte --help')


def main(argv=None):
    parser=Parser(prog='twine-edge-overlap',description='Reorganiza um arquivo Twee sem sobrescrever o original.')
    parser.add_argument('caminho',nargs='?',help='Caminho de um arquivo .twee com metadados de layout')
    actions=parser.add_mutually_exclusive_group()
    actions.add_argument('--prepare-runtime',action='store_true',help='Prepara os componentes para uso posterior sem internet.')
    actions.add_argument('--repair-runtime',action='store_true',help='Obtém novamente os componentes; requer internet.')
    parser.add_argument('--version',action='version',version='0.1.0.dev0')
    try:
        args=parser.parse_args(argv)
        action=args.prepare_runtime or args.repair_runtime
        if bool(args.caminho)==bool(action):
            raise InputError('Informe exatamente um caminho .twee OU uma ação de preparação; consulte --help')
        def progress(message): print(message,file=sys.stderr)
        if action:
            if args.repair_runtime: progress('Reparo solicitado: obter novamente o componente requer internet.')
            ensure_runtime(force_repair=args.repair_runtime,progress=progress)
            print('Componentes de processamento prontos para uso sem internet.')
            return 0
        result=run(args.caminho,progress=progress)
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
