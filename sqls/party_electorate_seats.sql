with ranked_votes as (
    select *,
        row_number() over (partition by electorate_id order by votes desc ) as rn
    from candidate_votes_rnz_preliminary
),
electorate_winner as (
    select electorate_id, party_id
    from ranked_votes
    where rn = 1
)
select party_id, count(*) as electorate_seats -- Independent candidates included (party_id is null)
from electorate_winner
group by party_id
