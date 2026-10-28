"""Render the entire registry and requirement/task coverage without changing support."""
import argparse
from collections import Counter
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from twine_edge_overlap.runtime_catalog import read_json,support_status


def span(first,last):return set(range(first,last+1))


def render(registry,tasks_text):
    targets=registry['targets']
    if len({target['id'] for target in targets})!=len(targets):raise ValueError('Duplicate support target')
    evidence=registry.get('evidence',{})
    states=Counter(support_status(target,evidence) for target in targets)
    tasks={int(number):flag.upper()=='X' for flag,number in re.findall(r'^- \[([ Xx])\] T(\d+)',tasks_text,re.M)}
    rows=['# Ledger integral de suporte','',
          'Gerado por `tools/runtime/report-support.py`; status derivado dos slots e evidÃªncias, sem alterar o registro.',
          'Contagens de tarefas sÃ£o rastreabilidade de trabalho, nÃ£o aprovaÃ§Ã£o de requisitos ou ambientes.',
          '',f"{len(targets)} cÃ©lulas; {sum(len(t['python_qualifications']) for t in targets)} slots Python; estados: {dict(states)}.",
          '', '| Alvo | Estado agregado | Python 3.12 | Python 3.14 | Ambiente Actions | Artefato qualificado | US1 AC1â€“3 |',
          '|---|---|---|---|---|---|---|']
    for target in targets:
        slots={slot['python_minor']:slot for slot in target['python_qualifications']}
        image=target.get('image_id') or 'pendente'
        artifact=target.get('artifact_id') or 'pendente'
        acceptance='pendentes' if target['os']=='linux' and support_status(target,evidence)!='validada' else ('ver evidÃªncias' if target['os']=='linux' else 'nÃ£o se aplica')
        rows.append(f"| `{target['id']}` | {support_status(target,evidence)} | {slots['3.12']['status']} | {slots['3.14']['status']} | {image} | {artifact} | {acceptance} |")
    rows+=['', '## Evidências e limites', '',
           '- Qualificação obrigatória por ABI/arquitetura/Python no GitHub Actions; as 69 distribuições/versões são declarações de compatibilidade.',
           '- Assinatura Developer ID e notarização macOS são opcionais, sem credenciais Apple como gate.',
           '- Estado derivado dos registros: resultados históricos não aprovam automaticamente uma ABI.',
           '- Integridade, instalação, corpus, offline, recuperação, licenças e revisão Twine continuam obrigat?rios.',
           '', '## FR-001?018 e SC-001?010', '',
           '| Requisito | Tarefas relacionadas | Tarefas verificadas | Gate de encerramento |',
           '|---|---|---|---|']
    mapping={}
    def add(keys,ids):
        for key in keys:mapping[key]=ids
    add(('FR-001','FR-002'),span(7,20)|span(24,34)|span(36,45)|span(49,56))
    add(('FR-003','FR-017','FR-018'),{2,13,32,33,70,74,75,81,82})
    add(('FR-004','FR-012'),{18,22,33,35,47,55,78,79})
    add(('FR-005',),{21,23,48,56,62,76}|span(36,45))
    add(('FR-006','FR-007'),{57,62,63,56}|span(36,45))
    add(('FR-008','FR-009'),span(58,61)|{64,65}|span(67,73))
    add(('FR-010','FR-011'),{10,15,16}|span(67,77))
    add(('FR-013',),{1,4,12,21,64,65})
    add(('FR-014',),{19,20,30,31,66,80}|span(49,52))
    add(('FR-015',),{11,32,62,71,80})
    add(('FR-016',),{3,56,76}|span(36,46)|span(62,66)|span(78,84))
    add(('SC-001','SC-004','SC-007'),span(22,56)|{78,79})
    add(('SC-002','SC-003','SC-006'),span(57,66))
    add(('SC-005',),span(67,77))
    add(('SC-008','SC-009','SC-010'),{2,3,70,74,75}|span(81,84))
    for key,ids in sorted(mapping.items()):
        if not ids.issubset(tasks):raise ValueError('Requirement maps to absent task')
        refs=', '.join(f'T{number:03}' for number in sorted(ids))
        checked=sum(tasks[number] for number in ids)
        rows.append(f'| {key} | {refs} | {checked}/{len(ids)} | pendente: evidÃªncias especÃ­ficas e sete alvos ABI completos |')
    return '\n'.join(rows)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry',type=Path,default=ROOT/'tools/runtime/abi-targets.json')
    parser.add_argument('--tasks',type=Path,default=ROOT/'specs/003-add-cross-platform-support/tasks.md')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    output=render(read_json(args.registry),args.tasks.read_text(encoding='utf-8'))
    with args.output.open('x',encoding='utf-8') as stream:stream.write(output)
    print('Full ledger written; no support status changed.')


if __name__=='__main__':main()
