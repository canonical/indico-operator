import http from 'k6/http';
import { sleep } from 'k6';

const params = {
  "headers": {
    'Host': 'indico.local',
  },
};

export default function () {
  http.get('http://{target_ip}', params);
  sleep(1);
}
