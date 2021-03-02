while :
do
    while getopts u:p:t:s:m:z: flag
    do
        case "${flag}" in
            u) username=${OPTARG};;
            p) password=${OPTARG};;
            t) tenant=${OPTARG};;
            s) server=${OPTARG};;
            m) monitoring=${OPTARG};;
            z) zone=${OPTARG};;
        esac
    done
    python3 auto-discovery.py -u $username -p $password -t $tenant -s $server -m $monitoring -z $zone;
    sleep 3600;
done
