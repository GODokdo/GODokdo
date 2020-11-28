import { INavData } from '@coreui/angular';
import { API_URL } from './api.service'
export const navItems: INavData[] = [
  {
    name: '오류 검출 현황',
    url: '/dashboard',
    icon: 'icon-speedometer',
    badge: {
      variant: 'info',
      text: 'NEW'
    }
  },
  {
    title: true,
    name: '표기 오류 검출'
  },
  {
    name: '수집된 문서',
    url: '/documents/list',
    icon: 'icon-drop'
  },  
  {
    name: '분석 요청',
    url: '/documents/post',
    icon: 'icon-drop'
  },
  {
    title: true,
    name: '기타'
  },
  {
    name: '오류 분류 수정',
    url: '/documents/errors',
    icon: 'icon-drop'
  },  
  {
    name: 'API document',
    url: API_URL,
    icon: 'icon-cloud-download',
    class: 'mt-auto',
    variant: 'success',
    attributes: { target: '_blank', rel: 'noopener' }
  },
  {
    name: 'ICT CoC',
    url: 'http://www.ictcoc.kr/03_pro_n/pro01_view.asp?idx=55',
    icon: 'icon-cloud-download',

    variant: 'danger',
    attributes: { target: '_blank', rel: 'noopener' }
  },
];
