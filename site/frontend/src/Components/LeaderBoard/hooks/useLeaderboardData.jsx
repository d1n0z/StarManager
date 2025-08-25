import {useEffect, useState} from "react";

const DICT_CATEGORY_NAME = {
    "Топ по монетам":       "topcoins",
    "Топ по сообщениям":    "topmessages",
    "Топ по дуэлям":        "topduels",
    "Топ по лиге":          "topleagues",
    "Топ по репутации":     "toprep",
    "Топ по примерам":      "topmath",
    "Топ по бонусам":       "topbonus",
}

function fetchDataCategory(paramCategory, offset, limit, setLeaderboardData) {
    fetch(`/api/leaderboard/${paramCategory}?offset=${offset}&limit=${limit}`)
        .then(res => res.json())
        .then((jsonDataCategory) => {
            setLeaderboardData(jsonDataCategory);
        })
        .catch(() => console.error("Error loading leaderboard data"));
}

export default function useLeaderboardData(textCategory, page, pageSize = 10) {
  const [data, setData] = useState({ total: 0, items: [] });
  useEffect(() => {
    const param = DICT_CATEGORY_NAME[textCategory];
    const offset = page * pageSize;
    fetch(`/api/leaderboard/${param}?offset=${offset}&limit=${pageSize}`)
      .then(res => res.json())
      .then(json => setData(json))
      .catch(console.error);
  }, [textCategory, page, pageSize]);

  return data;
}
