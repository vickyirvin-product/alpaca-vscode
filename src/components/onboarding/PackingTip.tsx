interface PackingTipProps {
  destination: string;
  activities: string[];
  timeOfYear: string;
}

export function PackingTip({ destination, activities, timeOfYear }: PackingTipProps) {
  const getTipData = (): { emoji: string; title: string; content: string } => {
    const destLower = destination.toLowerCase();
    const month = timeOfYear.toLowerCase();
    
    // Japan cherry blossom season
    if (destLower.includes('japan') && (month.includes('march') || month.includes('april'))) {
      return {
        emoji: "🌸",
        title: "Cherry blossom season!",
        content: "Pack layers for cool mornings and warm afternoons. Don't forget a good camera and comfortable walking shoes for temple visits."
      };
    }
    
    // Ski trips
    if (activities.some(a => a.toLowerCase().includes('ski') || a.toLowerCase().includes('snowboard'))) {
      return {
        emoji: "⛷️",
        title: "Ski trip essentials",
        content: "Don't forget lip balm with SPF, hand warmers, and a neck gaiter. Pack an extra pair of gloves in case one gets wet!"
      };
    }
    
    // Beach trips
    if (activities.some(a => a.toLowerCase().includes('beach'))) {
      return {
        emoji: "🏖️",
        title: "Beach vacation tip",
        content: "Pack reef-safe sunscreen, a waterproof phone case, and a lightweight beach bag. Bring aloe vera for those unexpected sunburns!"
      };
    }
    
    // Pool activities
    if (activities.some(a => a.toLowerCase().includes('pool'))) {
      return {
        emoji: "🏊",
        title: "Pool time!",
        content: "Remember to pack swim goggles, pool toys for the kids, and a quick-dry towel. Don't forget waterproof sunscreen!"
      };
    }
    
    // Theme parks
    if (activities.some(a => a.toLowerCase().includes('theme park'))) {
      return {
        emoji: "🎢",
        title: "Theme park pro tip",
        content: "Pack a small backpack with snacks, portable chargers, and band-aids. Wear comfortable, broken-in shoes - you'll be walking miles!"
      };
    }
    
    // Nice restaurants/events
    if (activities.some(a => a.toLowerCase().includes('restaurant') || a.toLowerCase().includes('event'))) {
      return {
        emoji: "🍽️",
        title: "Dining out?",
        content: "Pack at least one dressy outfit and comfortable dress shoes. A small clutch or crossbody bag is perfect for evening outings."
      };
    }
    
    // Camping
    if (activities.some(a => a.toLowerCase().includes('camping'))) {
      return {
        emoji: "🏕️",
        title: "Camping essentials",
        content: "Bring extra batteries, a headlamp, and layers for temperature changes. Pack trash bags and wet wipes - they're lifesavers!"
      };
    }
    
    // Hiking/Walking
    if (activities.some(a => a.toLowerCase().includes('hiking') || a.toLowerCase().includes('walking'))) {
      return {
        emoji: "🥾",
        title: "Hiking adventure",
        content: "Break in your hiking boots before the trip! Pack blister prevention tape, a reusable water bottle, and energy snacks."
      };
    }
    
    // Europe in summer
    if ((destLower.includes('europe') || destLower.includes('paris') || destLower.includes('london') || destLower.includes('rome')) &&
        (month.includes('june') || month.includes('july') || month.includes('august'))) {
      return {
        emoji: "🇪🇺",
        title: "European summer",
        content: "Pack light, breathable fabrics and comfortable walking shoes. Bring a small day pack and a reusable water bottle for sightseeing."
      };
    }
    
    // Tropical destinations
    if (destLower.includes('hawaii') || destLower.includes('caribbean') || destLower.includes('bali') || destLower.includes('thailand')) {
      return {
        emoji: "🌴",
        title: "Tropical paradise",
        content: "Pack lightweight, quick-dry clothing and insect repellent. Bring a waterproof bag for beach days and water activities!"
      };
    }
    
    // Cold weather destinations
    if (destLower.includes('iceland') || destLower.includes('norway') || destLower.includes('alaska') ||
        (month.includes('december') || month.includes('january') || month.includes('february'))) {
      return {
        emoji: "❄️",
        title: "Cold weather travel",
        content: "Layer up! Pack thermal underwear, wool socks, and a warm hat. Hand and toe warmers are game-changers for outdoor activities."
      };
    }
    
    // Default tip
    return {
      emoji: "✈️",
      title: "Travel smart",
      content: "Roll your clothes to save space, pack a change of clothes in your carry-on, and bring an empty water bottle to fill after security!"
    };
  };

  const tipData = getTipData();

  return (
    <div className="bg-accent/50 border border-accent rounded-xl p-4">
      <div className="flex items-start gap-3">
        <span className="text-2xl">{tipData.emoji}</span>
        <div>
          <h3 className="font-semibold text-secondary mb-1">{tipData.title}</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {tipData.content}
          </p>
        </div>
      </div>
    </div>
  );
}