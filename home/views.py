from django.shortcuts import render


CATEGORIES = [
    {
        'id': 100000,
        'name': '求人',
        'image': '/image/jobs.png',
    },
    {
        'id': 200000,
        'name': '住まい',
        'image': '/image/real-estate.png',
    },
    {
        'id': 300000,
        'name': '売ります',
        'image': '/image/sell.png',
    },
    {
        'id': 400000,
        'name': 'コミュニティ',
        'image': '/image/community.png',
    },
  
]

LOCATIONS = [
  {
    'id': 16002,
    'name': 'New South Wales',
    'image': '/image/nsw.jpg',
  },
  {
    'id': 16004,
    'name': 'Queensland',
    'image': '/image/qld.jpg',
  },
  {
    'id': 16007,
    'name': 'Victoria',
    'image': '/image/vic.jpg',
  },
  {
    'id': 16008,
    'name': 'Western Australia',
    'image': '/image/wa.jpg',
  },
]

def index(request):
    return render(request, 'home/index.html', {
        'categories': CATEGORIES,
        'locations': LOCATIONS
    })
