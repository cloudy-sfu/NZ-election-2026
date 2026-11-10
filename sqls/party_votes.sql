select partyId as party_id, sum(votes) as votes
from party_votes_rnz_preliminary
group by partyId
