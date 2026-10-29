"""Verify both recovery suites in the four already preserved native reports."""
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
digest = lambda raw: hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    summary_raw = (HERE / 'summary.json').read_bytes()
    summary = json.loads(summary_raw)
    references = {row['case'] for row in json.loads((ROOT / 'tests/fixtures/cases.json').read_bytes())
                  if row['known_resolvable']}
    require(len(references) == 6, 'Expected six public recovery references')

    def check_cases(rows):
        require(len(rows) == 6 and {row['case'] for row in rows} == references, 'Incomplete recovery references')
        require(all(row['after'] == [0, 0, 0] for row in rows), 'Recovery reference did not finish clean')
        for row in rows:
            for key in ('original_preserved', 'semantic_preserved'):
                if key in row:
                    require(row[key] is True, 'Recovery failed to preserve story data')

    rows = []
    for guest in summary['guests']:
        if guest['abi'] != 'glibc':
            continue
        for slot in guest['python_slots']:
            suffix = '/application/application-' + slot['minor'] + '.json.gz'
            matches = [row for row in guest['preserved_files'] if row['file'].endswith(suffix)]
            require(len(matches) == 1, 'Missing native installed report')
            path = HERE / matches[0]['file']
            raw = gzip.decompress(path.read_bytes())
            require(digest(raw) == slot['report_sha256'] == matches[0]['uncompressed_sha256'], 'Native report changed')
            report = json.loads(raw)
            primary = report['recovery']['scenarios']
            require(len(primary) == 8, 'Primary recovery suite is incomplete')
            for scenario in primary.values():
                check_cases(scenario['cases'])
            failed = report['observations']['explicit']['recovery']
            require(set(failed) == {'transfer', 'disk-space', 'execution-denied', 'corrupt-archive'}, 'Nested failed repairs missing')
            for name, scenario in failed.items():
                require(scenario['selected_generation_preserved'] is True and scenario['previous_handle_usable'] is True
                        and scenario['failed_repair_acquisition_calls'] == 1 and scenario['offline_acquisition_calls'] == 0,
                        'Nested repair changed generation or acquired offline')
                check_cases(scenario['references'])
                if name == 'execution-denied':
                    require(scenario['real_execution_denial'] is True, 'Execution denial was not real')
            processes = report['observations']['explicit']['process_recovery']
            require(processes['passed'] is True and processes['real_engine'] is True, 'Nested process suite failed')
            require(set(processes['scenarios']) == {'during_download', 'before_select', 'after_select', 'concurrent_first_use'}, 'Nested process scenarios missing')
            for name, scenario in processes['scenarios'].items():
                require(scenario['passed'] is True and scenario['old_handle_usable'] is True and scenario['offline_references'] == 6,
                        'Nested process recovery failed')
                check_cases(scenario['cases'])
                if name == 'concurrent_first_use':
                    require(scenario['acquisition_calls'] == 1 and scenario['same_generation'] is True
                            and scenario['workers'] == scenario['workers_ready'] == 2 and scenario['start_barrier'] is True,
                            'Concurrent workers did not share one generation/acquisition')
                else:
                    require(scenario['exitcode'] == 77 and scenario['lock_reacquired'] is True and scenario['orphan_untouched'] is True,
                            'Crash recovery/lock/orphan preservation failed')
            rows.append(dict(release=guest['release'], python=slot['python'], minor=slot['minor'],
                             report=matches[0]['file'], report_sha256=digest(raw),
                             compressed_report_sha256=digest(path.read_bytes()),
                             primary_scenarios=8, nested_failed_repairs=4, nested_process_scenarios=4,
                             scenario_executions=16, offline_reference_executions=96))
    require(len(rows) == 4, 'Expected both Python slots on both Ubuntu versions')
    result = dict(kind='verified-native-ubuntu-nested-recovery-review', qualified=False, approved=False,
                  revision=summary['revision'], native_summary_sha256=digest(summary_raw),
                  verifier_sha256=digest(Path(__file__).read_bytes()), reports=rows,
                  scenario_executions=sum(row['scenario_executions'] for row in rows),
                  offline_reference_executions=sum(row['offline_reference_executions'] for row in rows))
    with (HERE / 'nested-recovery.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(reports=len(rows), scenarios=result['scenario_executions'],
                          offline_references=result['offline_reference_executions'], passed=True)))


if __name__ == '__main__':
    main()
