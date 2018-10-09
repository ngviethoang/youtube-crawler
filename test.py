import subprocess

if __name__ == '__main__':
    subprocess.call([
        'python', 'youtube.py',
        '--q', 'ted talks',
        '--max-results', '100'
    ])
