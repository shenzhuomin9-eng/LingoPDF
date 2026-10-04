import json
import tempfile
import unittest
from pathlib import Path
from app.jobs import JobManager


class HistoryTests(unittest.TestCase):
    def test_finished_outputs_and_original_paths_survive_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            job_dir = root / 'history1'
            result = job_dir / '0' / 'results' / 'paper_zh.pdf'
            result.parent.mkdir(parents=True)
            result.write_bytes(b'pdf content')
            snapshot = {'id':'history1','status':'finished','engine':'google','lang_in':'en','lang_out':'zh',
                        'output_dir':'','dual':False,'skip_references':True,'created_at':1,'elapsed':1,
                        'files':[{'name':'paper.pdf','size':20,'source_path':str(root / 'paper.pdf'),
                                  'source_id':None,'status':'done','outputs':[{'name':result.name,'path':str(result)}]}]}
            (job_dir / 'job.json').write_text(json.dumps(snapshot),encoding='utf-8')
            manager = JobManager(history_dir=root)
            job = manager.get('history1')
            self.assertIsNotNone(job)
            self.assertEqual(job.files[0].source_path,root / 'paper.pdf')
            self.assertEqual(job.files[0].outputs[0]['path'],str(result))


if __name__ == '__main__':
    unittest.main()
