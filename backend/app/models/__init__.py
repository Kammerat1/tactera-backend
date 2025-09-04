# tactera_backend/models/__init__.py
# Centralized imports for all database models and schemas

# Manager
from .manager_model import Manager, ManagerRegister, ManagerLogin

# Club
from .club_model import Club
from .club_schemas import ClubRegister

# League
from .league_model import League

# Player and stats
from .player_model import Player, PlayerRead, InjuryRead, ContractSummary
from .player_stat_model import PlayerStat

# Stat level requirements
from .stat_level_requirement_model import StatLevelRequirement

# Training
from .training_model import TrainingGround, TrainingHistory, TrainingHistoryStat

# Match and results
from .match_model import Match, MatchResult

# Season state
from .season_model import SeasonState

# Country
from .country_model import Country

# Stadium
from .stadium_model import Stadium, StadiumPart

# Suspension
from .suspension_model import Suspension

# Injury
from .injury_model import Injury

# Formation system
from .formation_model import (
    FormationTemplate, ClubFormation, FormationTemplateRead, ClubFormationRead, 
    FormationUpdateRequest, MatchSquad, MatchSubstitution, SubstitutionRequest, 
    SubstitutionRead, MatchSquadRead, SubstitutionValidationResponse
)

# Contract and transfer system - NEW
from .contract_model import (
    PlayerContract, TransferListing, TransferBid, ContractPreference, 
    TransferType, AuctionStatus, ContractRead, TransferListingRead,
    CreateAuctionRequest, CreateTransferListRequest, PlaceBidRequest,
    TransferBidRead, ContractOfferRequest, ContractOfferResponse
)