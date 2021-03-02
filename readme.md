# Описание #
auto-discovery.py получает список машин Y2 из vRA, проверяет доступен ли на них exporter по порту 9100.  
Сопсотавляет полученный список с машинами в prometheus.yml в job'ах node-exporter и windows-exporter.  
Если vRA появилась машина, которой нет в указанных job'ах, auto-discovery.py добавит машину в соответствующую job.  
Если в указанных job'ах есть машина, которой нету в vRA, auto-discovery.py удалит машину из мониторинга. 
Jenkinsfile - pipeline для Jenkins job для автоматизированной сборки сервиса auto-discovery в образ контейнера; для доставки образа и запуска контейнера на сервере мониторинга.
playbook.yml - ansible-роль, реализующая запуск сервиса uto-discovery на сервере мониторинга. Запускается на сервере AWX. 

# Usage #
### Python ###
python3 ./auto-discovery.py -u $VRA_RESTAPI_USER -p $VRA_RESTAPI_PASSWORD

### Docker ###
docker build -t auto-discovery .  
docker run -d --name auto-discovery -v $PATH_TO_PROM_CONFIG/prometheus.yml:/app/prometheus.yml auto-discovery -u $VRA_RESTAPI_USER -p $VRA_RESTAPI_PASSWORD

# Пример #
2020-12-18 06:40:10,903 INFO Bearer token obtained successfully  
2020-12-18 06:40:12,337 INFO Serching for machines to add or to remove from monitoring...  
2020-12-18 06:40:16,307 WARNING Exporter on 10.1.0.62:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:40:16,341 WARNING Exporter on test.dev2.y2.pis.cbr.ru:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:40:16,829 WARNING Exporter on 10.1.0.115:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:40:17,113 WARNING Exporter on dup.dev2.y2.pis.cbr.ru:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:40:17,575 WARNING Exporter on 10.1.0.133:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:40:17,652 WARNING Exporter on cicd01.dev.y2.pis.cbr.ru:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:40:17,810 INFO Exporter on control.dev.y2.pis.cbr.ru:9100 is responding. Machine can be added to monitoring  
2020-12-18 06:40:18,769 INFO Added machine to monitoring: control.dev.y2.pis.cbr.ru  
2020-12-18 06:40:18,886 INFO Removed machine from monitoring: rmme.dev2.y2.pis.cbr.ru  
2020-12-18 06:40:18,886 INFO Removed windows machine from monitoring: windows.dev2.y2.pis.cbr.ru  
2020-12-18 06:45:19,354 INFO Running job Every 5 minutes do job() (last run: [never], next run: 2020-12-18 06:45:18)  
2020-12-18 06:45:19,355 INFO Serching for machines to add or to remove from monitoring...  
2020-12-18 06:45:25,584 WARNING Exporter on 10.1.0.133:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:45:25,623 WARNING Exporter on dup.dev2.y2.pis.cbr.ru:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:45:25,907 WARNING Exporter on 10.1.0.115:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:45:25,990 WARNING Exporter on test.dev2.y2.pis.cbr.ru:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:45:27,587 WARNING Exporter on 10.1.0.62:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:45:27,936 WARNING Exporter on cicd01.dev.y2.pis.cbr.ru:9100 is not responding. Unable add machine to monitoring  
2020-12-18 06:45:29,254 INFO Nothing to do. Everything is up to date
