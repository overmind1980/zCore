import pexpect
import sys

TIMEOUT = 300
ZCORE_PATH = '../zCore'
OUTPUT_FILE = 'test-output.txt'
RESULT_FILE = 'test-result.txt'
CHECK_FILE = 'test-check-passed.txt'
TEST_CASE_FILE = 'testcases.txt'


class Tee:
    def __init__(self, name, mode):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self

    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.file.flush()


with open(TEST_CASE_FILE, "r") as f:
    lines = f.readlines()
    positive = [line for line in lines if not line.startswith('-')]
    negative = [line[1:] for line in lines if line.startswith('-')]
    test_filter = (','.join(positive) + '-' + ','.join(negative)).replace('\n', '')

child = pexpect.spawn("make -C %s test mode=release test_filter='%s'" % (ZCORE_PATH, test_filter),
                      timeout=TIMEOUT, encoding='utf-8')
child.logfile = Tee(OUTPUT_FILE, 'w')

index = child.expect(['finished!', 'panicked', pexpect.EOF, pexpect.TIMEOUT])
result = ['FINISHED', 'PANICKED', 'EOF', 'TIMEOUT'][index]
print(result)

passed = []
failed = []
passed_case = set()
with open(OUTPUT_FILE, "r") as f:
    for line in f.readlines():
        if line.startswith('[       OK ]'):
            passed += line
            passed_case.add(line[13:].split(' ')[0])
        elif line.startswith('[  FAILED  ]') and line.endswith(')\n'):
            failed += line

with open(RESULT_FILE, "w") as f:
    f.writelines(passed)
    f.writelines(failed)

with open(CHECK_FILE, 'r') as f:
    check_case = set([case.strip() for case in f.readlines()])

not_passed = check_case - passed_case
if not_passed:
    print('=== Failed cases ===')
    for case in not_passed:
        print(case)
    exit(1)
else:
    print('All checked case passed!')
