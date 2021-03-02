pipeline {
    agent { node { label 'slave' } }
    stages {
        stage('build') {
                steps {
                    script {
                        if (params.BUILD) {
                        sh """
                            sed -i \"s/FROM /FROM ${params.ARTIFACTORY_TRUSTED_REGISTRY}/g\" Dockerfile
                            docker build -t ${params.ARTIFACTORY_TRUSTED_REGISTRY}/y2/auto-discovery:latest .
                            docker push ${params.ARTIFACTORY_TRUSTED_REGISTRY}/y2/auto-discovery:latest
                        """
                    }
                }
            }
        }
        stage('deploy') {
            agent {
                docker {
                    alwaysPull true
                    image "${params.DOCKER_AGENT_IMAGE}"            
                    args "-u root"     
                    registryUrl "${params.ARTIFACTORY_REGISTRY_URL}"
                    registryCredentialsId "${params.ARTIFACTORY_CREDENTIALS}"
                }
            }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: "${params.ARTIFACTORY_CREDENTIALS}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        withCredentials([usernamePassword(credentialsId: "${params.VRA_CREDENTIALS}", usernameVariable: 'VRA_USER', passwordVariable: 'VRA_PASS')]) {
                            withCredentials([usernamePassword(credentialsId: "${params.AWX_CREDENTIALS}", usernameVariable: 'AWX_USER', passwordVariable: 'AWX_PASS')]) {
                                sh("tower-cli config host ${AWX_HOST} && tower-cli config username $AWX_USER && tower-cli config password $AWX_PASS && tower-cli config verify_ssl False")
                                sh("tower-cli job launch --monitor --insecure -e registry_user='$DOCKER_USER' -e registry_password='$DOCKER_PASS' -e registry_host='$ARTIFACTORY_TRUSTED_REGISTRY' -e prom_config_path='${PROM_CONFIG_PATH}' -e vra_server='${VRA_SERVER}' -e vra_tenant='${VRA_TENANT}' -e vra_restapi_user='$VRA_USER' -e vra_restapi_password='$VRA_PASS' -e monitoring_server='${MONITORING_SERVER}' -e y2_zone='${Y2_ZONE}' -J deploy-auto-discovery --inventory y2")
                            }
                        }
                    }
                }
            }
        }
    }
    post {
        always { cleanWs() }
        success { echo 'I succeeded' }
        failure { echo 'I failed' }
    }
}