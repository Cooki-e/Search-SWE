"""Check the build-to-search permission boundary without touching host task paths."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class IndexBoundaryTests(unittest.TestCase):
    def test_permissions_revoked_before_hidden_queries(self):
        script = Path(__file__).with_name("test.sh").read_text()
        build = script.index('run_phase "$BUILD_TIMEOUT_SECONDS"')
        stop = script.index('stop_submission_processes', build)
        revoke = script.index('if ! revoke_corpus_access', stop)
        stage = script.index('/tests/data/queries.jsonl', revoke)
        run = script.index('run_phase "$RUN_TIMEOUT_SECONDS"', stage)
        self.assertLess(build, stop)
        self.assertLess(stop, revoke)
        self.assertLess(revoke, stage)
        self.assertLess(stage, run)
        self.assertNotIn('rm -rf -- "$CORPUS_DIR"', script)

    @unittest.skipUnless(os.geteuid() == 0, "needs root to exercise submission UID permissions")
    def test_corpus_retained_but_submission_cannot_read_or_restore_access(self):
        for kind in ("uid", "gid"):
            mapping = Path(f"/proc/self/{kind}_map")
            if mapping.is_file():
                ranges = [list(map(int, row.split())) for row in mapping.read_text().splitlines()]
                if not any(start <= 10001 < start + count for start, _, count in ranges):
                    self.skipTest("needs mapped submission UID/GID 10001 outside the restricted user namespace")
        script = Path(__file__).with_name("test.sh").read_text()
        function = "revoke_corpus_access() {" + script.split("revoke_corpus_access() {", 1)[1].split("\n}", 1)[0] + "\n}"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o755)
            corpus = root / "corpus"
            corpus.mkdir(mode=0o750)
            corpus.chmod(0o750)
            os.chown(corpus, 0, 10001)
            pdf = corpus / "fixture.pdf"
            pdf.write_bytes(b"unchanged fixture PDF")
            os.chown(pdf, 0, 10001)
            pdf.chmod(0o440)
            inventory = corpus / "sentences.jsonl"
            inventory.write_text('{"sentence_id":"fixture","text":"Original sentence."}\n')
            os.chown(inventory, 0, 10001)
            inventory.chmod(0o440)
            inode = pdf.stat().st_ino
            # A second link outside the locked directory must also lose access.
            link = root / "corpus-link.pdf"
            os.link(pdf, link)

            def as_submission(command, path):
                return subprocess.run([*command, str(path)],
                                      user=10001, group=10001, extra_groups=[],
                                      capture_output=True, text=True, env={"LANG": "C", "PATH": "/usr/bin:/bin"})

            read = ["/usr/bin/head", "-c", "1"]
            self.assertEqual(as_submission(read, pdf).returncode, 0)
            self.assertEqual(as_submission(read, inventory).returncode, 0)
            subprocess.run(["bash", "--noprofile", "--norc", "-c",
                            function + '\nrevoke_corpus_access'],
                           env={"PATH": "/usr/bin:/bin", "CORPUS_DIR": str(corpus)}, check=True)
            self.assertEqual(pdf.read_bytes(), b"unchanged fixture PDF")
            self.assertEqual(pdf.stat().st_ino, inode)
            self.assertEqual(pdf.stat().st_mode & 0o777, 0o400)
            self.assertEqual(corpus.stat().st_mode & 0o777, 0o700)
            self.assertEqual(inventory.stat().st_mode & 0o777, 0o400)
            for path in (pdf, inventory, link):
                result = as_submission(read, path)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Permission denied", result.stderr)
            result = as_submission(["/usr/bin/chmod", "0755"], corpus)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Operation not permitted", result.stderr)

    def test_grader_has_private_corpus(self):
        source = Path(__file__).with_name("grader.py").read_text()
        self.assertIn('CORPUS_DIR = Path("/tests/corpus")', source)


if __name__ == "__main__":
    unittest.main()
