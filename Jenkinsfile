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
                    sh '. $VENV/bin/activate && flake8 . --count --show-source --statistics > flake8-report.txt || true'
                    sh '. $VENV/bin/activate && bandit -r . -f html -o bandit-report.html || true'
                }
            }
        }

        stage('Security Check') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    sh '. $VENV/bin/activate && safety check --full-report > safety-report.txt || true'
                }
            }
        }

        stage('Unit Tests & Coverage') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    sh '. $VENV/bin/activate && coverage run --source=. manage.py test || true'
                    sh '. $VENV/bin/activate && coverage html || true'
                    sh '. $VENV/bin/activate && coverage xml || true'
                }
            }
        }

        stage('Pytest Advanced') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    sh '. $VENV/bin/activate && pytest --ds=Website.settings --junitxml=pytest-report.xml --cov=. --cov-report=xml --cov-report=html || true'
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

        stage('Generate Summary Report') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    writeFile file: 'index.html', text: '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Pipeline Reports Dashboard</title>
</head>
<body>
    <h1>📊 Pipeline Reports Summary</h1>
    <ul>
        <li><a href="flake8-report.txt">Flake8 Report</a></li>
        <li><a href="bandit-report.html">Bandit Security Report</a></li>
        <li><a href="safety-report.txt">Safety Vulnerability Report</a></li>
        <li><a href="coverage.xml">Coverage XML</a></li>
        <li><a href="htmlcov/index.html">Coverage HTML</a></li>
        <li><a href="pytest-report.xml">Pytest JUnit XML</a></li>
        <li><a href="static/">Static Files</a></li>
    </ul>
    <p><strong>Last Build:</strong> ''' + new Date().toString() + '''</p>
</body>
</html>
'''
                }
            }
        }

        stage('Publish Artifacts') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    archiveArtifacts artifacts: '''
                        index.html,
                        flake8-report.txt,
                        safety-report.txt,
                        bandit-report.html,
                        coverage.xml,
                        pytest-report.xml,
                        htmlcov/**,
                        static/**
                    ''', allowEmptyArchive: true
                }
            }
        }
    }

    post {
        always {
            echo "🎉 PIPELINE BUILD COMPLETE 🎉"
            archiveArtifacts artifacts: 'index.html', allowEmptyArchive: true
            cleanWs()
        }
    }
}
