from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import for Code LLaMA and StarCoder integration (placeholder)
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
except ImportError:
    AutoModelForCausalLM = None
    AutoTokenizer = None
    torch = None

app = FastAPI()

# Allow CORS for frontend running on different origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Smart Contract Templates
CONTRACT_TEMPLATES = {
    "erc20": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract CustomToken is ERC20, Ownable {
    constructor(string memory name, string memory symbol, uint256 initialSupply) 
        ERC20(name, symbol) {
        _mint(msg.sender, initialSupply * 10 ** decimals());
    }

    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}""",
    "defi_vault": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DeFiVault is ReentrancyGuard, Ownable {
    IERC20 public token;
    mapping(address => uint256) public balances;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdraw(address indexed user, uint256 amount);
    
    constructor(address _token) {
        token = IERC20(_token);
    }
    
    function deposit(uint256 amount) external nonReentrant {
        require(amount > 0, "Amount must be greater than 0");
        token.transferFrom(msg.sender, address(this), amount);
        balances[msg.sender] += amount;
        emit Deposit(msg.sender, amount);
    }
    
    function withdraw(uint256 amount) external nonReentrant {
        require(amount > 0, "Amount must be greater than 0");
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        token.transfer(msg.sender, amount);
        emit Withdraw(msg.sender, amount);
    }
}""",
    "nft_marketplace": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract NFTMarketplace is ReentrancyGuard, Ownable {
    struct Listing {
        address seller;
        uint256 price;
        bool active;
    }
    
    mapping(address => mapping(uint256 => Listing)) public listings;
    uint256 public feePercentage = 250; // 2.5%
    
    event ItemListed(address indexed nft, uint256 indexed tokenId, uint256 price);
    event ItemSold(address indexed nft, uint256 indexed tokenId, address buyer, uint256 price);
    
    function listItem(address nft, uint256 tokenId, uint256 price) external {
        require(price > 0, "Price must be greater than 0");
        IERC721(nft).transferFrom(msg.sender, address(this), tokenId);
        
        listings[nft][tokenId] = Listing({
            seller: msg.sender,
            price: price,
            active: true
        });
        
        emit ItemListed(nft, tokenId, price);
    }
    
    function buyItem(address nft, uint256 tokenId) external payable nonReentrant {
        Listing storage listing = listings[nft][tokenId];
        require(listing.active, "Item not listed");
        require(msg.value >= listing.price, "Insufficient payment");
        
        uint256 fee = (listing.price * feePercentage) / 10000;
        uint256 sellerAmount = listing.price - fee;
        
        listing.active = false;
        payable(listing.seller).transfer(sellerAmount);
        IERC721(nft).transferFrom(address(this), msg.sender, tokenId);
        
        emit ItemSold(nft, tokenId, msg.sender, listing.price);
    }
}"""
}

def generate_smart_contract(prompt: str) -> str:
    # Check for specific contract types in prompt
    if "erc20" in prompt.lower() or "token" in prompt.lower():
        return CONTRACT_TEMPLATES["erc20"]
    elif "defi" in prompt.lower() or "vault" in prompt.lower():
        return CONTRACT_TEMPLATES["defi_vault"]
    elif "nft" in prompt.lower() or "marketplace" in prompt.lower():
        return CONTRACT_TEMPLATES["nft_marketplace"]
    
    # Default to ERC20 template
    return CONTRACT_TEMPLATES["erc20"]

@app.post("/chat")
async def chat(message: str = Form(...)):
    # Specialized handling for smart contract generation
    if any(keyword in message.lower() for keyword in ["smart contract", "solidity", "contract", "erc20", "nft", "defi"]):
        contract_code = generate_smart_contract(message)
        response = f"Here is the generated smart contract:\n```solidity\n{contract_code}\n```"
    elif "full app" in message.lower() or "complete app" in message.lower() or "full project" in message.lower():
        project = {
            "files": [
                {
                    "filename": "Token.sol",
                    "content": CONTRACT_TEMPLATES["erc20"]
                },
                {
                    "filename": "DeFiVault.sol",
                    "content": CONTRACT_TEMPLATES["defi_vault"]
                },
                {
                    "filename": "NFTMarketplace.sol",
                    "content": CONTRACT_TEMPLATES["nft_marketplace"]
                },
                {
                    "filename": "README.md",
                    "content": "# Smart Contract Project\nThis project includes ERC20 token, DeFi vault, and NFT marketplace implementations."
                }
            ]
        }
        import json
        response = f"Here is a full smart contract project:\n{json.dumps(project)}"
    else:
        response = f"Echo: {message}"
    return JSONResponse(content={"response": response})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"uploaded_files/{file.filename}"
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename, "message": "File uploaded successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
