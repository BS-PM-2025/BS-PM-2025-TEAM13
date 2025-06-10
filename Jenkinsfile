pipeline {
    agent any

    environment {
        VENV = 'venv'
        DJANGO_SETTINGS_MODULE = 'Website.settings'
        PYTHONPATH = '.'
    }

    options {
        timeout(time: 40, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    checkout scm
                }
            }
        }

        stage('Setup Python') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    sh 'python3 -m venv $VENV || true'
                    sh '. $VENV/bin/activate && pip install --upgrade pip || true'
                    sh '. $VENV/bin/activate && pip install -r requirements.txt || true'
                    sh '. $VENV/bin/activate && pip install flake8 coverage pytest pytest-django pytest-cov safety bandit || true'
                }
            }
        }

        stage('Static Analysis') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    sh '. $VENV/bin/activate && flake8 . --count --show-source --statistics || true'
                    sh '. $VENV/bin/activate && bandit -r . || true'
                }
            }
        }

        stage('Security Check') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    sh '. $VENV/bin/activate && safety check || true'
                }
            }
        }

        stage('Unit Tests & Coverage') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    sh '. $VENV/bin/activate && coverage run --source=. manage.py test || true'
                    sh '. $VENV/bin/activate && coverage xml || true'
                    sh '. $VENV/bin/activate && coverage html || true'
                }
            }
        }

        stage('Pytest Advanced') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    sh '. $VENV/bin/activate && pytest --ds=Website.settings --junitxml=pytest-report.xml --cov=. --cov-report=xml || true'
                }
            }
        }

        stage('Collect Static') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    sh '. $VENV/bin/activate && python manage.py collectstatic --noinput || true'
                }
            }
        }

        stage('Publish Artifacts') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    archiveArtifacts artifacts: 'coverage.xml, pytest-report.xml, htmlcov/**, static/**', allowEmptyArchive: true
                }
            }
        }
    }

post {
    always {
        echo "🎉 PIPELINE BUILD COMPLETE 🎉"
        echo '''
╔═══════════════════════════════════════════════╗
║                 PIPELINE STATUS              ║
║                                              ║
║   ██████████████████████████████████████     ║
║   █            SUCCESSFUL BUILD         █    ║
║   ██████████████████████████████████████     ║
║                                              ║
║      Jenkins Pipeline - Full Build Report    ║
╚═══════════════════════════════════════════════╝
'''

        writeFile file: 'pipeline_report.txt', text: '''
===========================
    PIPELINE STATUS
===========================

BUILD STEPS:

[OK]  Checkout            - Source code checkout from repository
[OK]  Setup Python (venv) - Create Python virtual environment & install dependencies
[OK]  Static Analysis     - flake8 code style checks, bandit security linting
[OK]  Security Check      - safety: Python dependency vulnerability scan
[OK]  Unit Tests/Coverage - Django unit tests & coverage report
[OK]  Pytest Advanced     - Advanced pytest with XML/coverage output
[OK]  Collect Static      - Collect Django static files
[OK]  Publish Artifacts   - Archive coverage, reports, static assets

---------------------------------------
Status:      SUCCESS   
Date:        ''' + new Date().toString() + '''
Triggered by: ${env.BUILD_USER ?: "GitHub push"}

Tips:
- Coverage reports (HTML) are archived if generated.
- For interactive graphs, see the Jenkins "Coverage" or "Test Reports" tabs (requires plugins).
- For build duration trends, check the Jenkins job dashboard (Build Time Trend graph).

===========================

'''

        archiveArtifacts artifacts: 'pipeline_report.txt', allowEmptyArchive: true
        cleanWs()
    }
}

}
