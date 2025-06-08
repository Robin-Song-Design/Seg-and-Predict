// 实际的颜色映射表  
const CITYSCAPES_COLORS = {  
    person: { color: 'rgb(150,5,61)', label: 'Person', id: 1 },  
    sign: { color: 'rgb(255,5,153)', label: 'Sign', id: 2 }, 
    wall: { color: 'rgb(120,120,120)', label: 'Wall', id: 3 },  
    building: { color: 'rgb(180,120,120)', label: 'Building', id: 4 },  
    trash: { color: 'rgb(173,0,255)', label: 'trash', id: 5 },
    sky: { color: 'rgb(6,230,230)', label: 'Sky', id: 6 },  
    floor: { color: 'rgb(80,50,50)', label: 'Floor', id: 7 },  
    tree: { color: 'rgb(4,200,3)', label: 'Tree', id: 8 },  
    road: { color: 'rgb(140,140,140)', label: 'Road', id: 9 },  
    streetlight: { color: 'rgb(0,71,255)', label: 'light', id: 10 },  
    sidewalk: { color: 'rgb(235,255,7)', label: 'Side', id: 11 },  
    trade:{ color: 'rgb(235,255,7)', label: 'Trade', id: 12 },  
    plant: { color: 'rgb(133,255,0)', label: 'Plant', id: 13 },  
    car: { color: 'rgb(0,102,200)', label: 'Car', id: 14 },  
    fence: { color: 'rgb(255,184,6)', label: 'Fence', id: 15 },  
    rock: { color: 'rgb(255,41,10)', label: 'Rock', id: 16 },  
    pole: { color: 'rgb(51,0,255)', label: 'Pole', id: 17 },  
    land: { color: 'rgb(0,194,255)', label: 'Land', id: 18 },  
    door: { color: 'rgb(8,255,51)', label: 'Door', id: 19 }, 
    earth: { color: 'rgb(120,120,7)', label: 'Earth', id: 20 }
};  