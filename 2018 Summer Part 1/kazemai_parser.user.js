// ==UserScript==
// @name            Kazemai Data Parser 
// @author          Kenton Lam
// @version         0.1.0
// @description     Parses various data from kazemai.
// @match           https://kazemai.github.io/fgo-vz/*
// ==/UserScript==

(function() {

    const translation = {
        '消耗': '',
        
        '淡水': 'water',
        '食料': 'food',
        '木材': 'wood',
        '石材': 'stone',
        '鐵材': 'iron',
        
        '叢林冒險': 'jungle',
        '觀景點': 'mountains',
        '私人沙灘': 'beach',
        '野餐之地': 'fields',
        '浪漫洞穴': 'cavern',
        '神秘區域': 'forest',

        '初級': 'beginner',
        '中級': 'intermediate',
        '上級': 'advanced',
        '超級': 'expert',
        '雷級': 'thunder',
        '嵐級': 'storm',
        
    };

    let translation_regex = [];
    for (const ch in translation) {
        if (translation.hasOwnProperty(ch)) {
            const en = translation[ch];
            translation_regex.push([new RegExp(ch, 'g'), en]);
        }
    }

    function _t(input) {
        for (let i = 0; i < translation_regex.length; i++) {
            const element = translation_regex[i];
            input = input.replace(element[0], element[1]);
        }
        return input;
    }

    function parseOneNode(table, filterItems) {
        let name = _t(table.firstElementChild.firstElementChild.textContent);

        let hasDrops = false;
        let drops = {};

        let dropRow = table.firstElementChild.lastElementChild;
        let dropTable = dropRow.querySelector('tbody');
        let itemIconsRow = dropTable.firstElementChild.querySelectorAll('div.itemST');
        let chancesRow = dropTable.children[1].children;
        for (let i = 0; i < itemIconsRow.length; i++) {
            const element = itemIconsRow[i];
            let itemType = _t(element.getAttribute('title'));
            if (filterItems === undefined || filterItems.indexOf(itemType) !== -1) {
                hasDrops = true;
                let itemsPerStack = parseInt(element.textContent);
                if (isNaN(itemsPerStack))
                    itemsPerStack = 1;
                
                let chance = parseFloat(chancesRow[i].textContent.split('%')[0].replace(/,/g, ''))/100;
                if (drops[itemType] === undefined) {
                    drops[itemType] = {
                        'initial': 0,
                        'stacks': 0,
                    };
                }
                drops[itemType]['initial'] += chance * itemsPerStack;
                drops[itemType]['stacks'] += chance;                
            }
        }
        return drops;
    }

    function parseOpenNodes(filterItems) {
        let nodes = new Map();
        for (const openDropDown of getOpenBlocks()) {
            for (let j = 0; j < openDropDown.children.length; j++) {
                const table = openDropDown.children[j];
                nodes[_t(table.querySelector('th').textContent)] = parseOneNode(table, filterItems);
            }
        }
        setOutput(nodes);
        return nodes;
    }

    function closeAll() {
        for (let open of getOpenBlocks()) {
            open.previousElementSibling.click();
        }
    }
    
    function parseSummerFarming() {
        var dt_list = document.querySelector('dl.accordion')
            .querySelectorAll('dt');
        
        openDropDowns(['主線關卡', '漂流物發現！', '耀眼夏日', '開拓計畫'], true);
        parseOpenNodes(['water', 'food', 'wood', 'stone', 'iron']);
    }

    function openDropDowns(list, exclude) {
        var dt = document.querySelectorAll('.accordion > dt');
        for (let i = 0; i < dt.length; i++) {
            let inList = list.indexOf(_t(dt[i].textContent)) !== -1;
            let willOpen = exclude ? (!inList) : inList;
            if (willOpen != dt[i].classList.contains('open')) 
                dt[i].click();
        }
    }

    function* getOpenBlocks() {
        let open = document.querySelectorAll('.accordion > .open');
        for (let i = 0; i < open.length; i++) {
            yield open[i].nextElementSibling;
        }
    }

    function parseSummerDevelopments() {
        openDropDowns(['開拓計畫']);
        let nameRegex = /^[^\d]*(\d+ [A-C]).*$/;
        let projects = new Map();
        for (const open of getOpenBlocks()) {
            for (let i = 0; i < open.children.length; i++) {
                const projectTable = open.children[i];
                let tbody = projectTable.querySelector('tbody');
                let header = tbody.firstElementChild.textContent;
                let name = 'Project '+nameRegex.exec(header)[1];

                let materials = _t(tbody.children[1].firstElementChild.textContent).split('/');
                let materialCounts = tbody.children[2].firstElementChild.textContent.split('/');

                let data = new Map();
                for (let i = 0; i < materials.length; i++) {
                    data[materials[i]] = parseInt(materialCounts[i]);
                }
                projects[name] = data;
            }
            break;
        }

        setOutput(projects);
        
    }

    function setOutput(obj) {
        output.value = JSON.stringify(
            obj,
            undefined, 2);
    }

    var docFrag = document.createDocumentFragment();

    var article = document.querySelector('article.content');

    var closeButton = document.createElement('button');
    closeButton.textContent = 'Collapse All';
    closeButton.addEventListener('click', closeAll);
    docFrag.appendChild(closeButton);

    var button = document.createElement('button');
    button.textContent = 'Parse Summer';
    button.addEventListener('click', parseSummerFarming);
    docFrag.appendChild(button);

    var button2 = document.createElement('button');
    button2.textContent = 'Parse Summer Developments';
    button2.addEventListener('click', parseSummerDevelopments);
    docFrag.appendChild(button2);

    var output = document.createElement('textarea');
    docFrag.appendChild(document.createElement('br'));
    docFrag.appendChild(output);

    article.insertBefore(docFrag, article.firstChild);
})();