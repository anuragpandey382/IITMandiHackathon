'use client';

import { useState } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  MessageSquare, 
  Users, 
  AlertTriangle, 
  Search, 
  Filter,
  Calendar,
  Download
} from 'lucide-react';

export default function AdminDashboard() {
  const [selectedTab, setSelectedTab] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  
  // Dummy data for chat logs
  const chatLogs = [
    { 
      id: 1, 
      user: { 
        name: "Aditya Sharma", 
        email: "aditya.sharma@gmail.com", 
        avatar: "https://ui.shadcn.com/avatars/01.png" 
      },
      messageCount: 24,
      lastActive: "2 minutes ago",
      duration: "18 mins",
      status: "active",
      topic: "MATLAB: Undefined function or variable error",
      flagged: false
    },
    { 
      id: 2, 
      user: { 
        name: "Priya Patel", 
        email: "priya.patel@gmail.com", 
        avatar: "https://ui.shadcn.com/avatars/03.png" 
      },
      messageCount: 8,
      lastActive: "15 minutes ago",
      duration: "6 mins",
      status: "completed",
      topic: "MATLAB: Array dimensions must match for binary operation",
      flagged: false
    },
    { 
      id: 3, 
      user: { 
        name: "Raj Malhotra", 
        email: "raj.malhotra@outlook.com", 
        avatar: "https://ui.shadcn.com/avatars/02.png" 
      },
      messageCount: 32,
      lastActive: "1 hour ago",
      duration: "24 mins",
      status: "completed",
      topic: "MATLAB: Index exceeds matrix dimensions",
      flagged: true
    },
    { 
      id: 4, 
      user: { 
        name: "Sneha Gupta", 
        email: "sneha.gupta@yahoo.com", 
        avatar: "https://ui.shadcn.com/avatars/04.png" 
      },
      messageCount: 16,
      lastActive: "2 hours ago",
      duration: "12 mins",
      status: "completed",
      topic: "MATLAB: Invalid MEX-file or file not found",
      flagged: false
    },
    { 
      id: 5, 
      user: { 
        name: "Vikram Singh", 
        email: "vikram.singh@gmail.com", 
        avatar: "https://ui.shadcn.com/avatars/05.png" 
      },
      messageCount: 5,
      lastActive: "Just now",
      duration: "4 mins",
      status: "active",
      topic: "MATLAB: Subscripted assignment dimension mismatch",
      flagged: false
    },
    { 
      id: 6, 
      user: { 
        name: "Meera Krishnan", 
        email: "meera.krishnan@gmail.com", 
        avatar: "https://ui.shadcn.com/avatars/06.png" 
      },
      messageCount: 18,
      lastActive: "45 minutes ago",
      duration: "15 mins",
      status: "completed",
      topic: "MATLAB: Too many input arguments error",
      flagged: false
    },
    { 
      id: 7, 
      user: { 
        name: "Arjun Reddy", 
        email: "arjun.reddy@hotmail.com", 
        avatar: "https://ui.shadcn.com/avatars/07.png" 
      },
      messageCount: 12,
      lastActive: "30 minutes ago",
      duration: "9 mins",
      status: "completed",
      topic: "MATLAB: License checkout failed error",
      flagged: true
    }
  ];


  // Filter chats based on selected tab and search query
  const filteredChats = chatLogs.filter(chat => {
    const matchesSearch = chat.user.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          chat.topic.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (selectedTab === "all") return matchesSearch;
    if (selectedTab === "active") return chat.status === "active" && matchesSearch;
    if (selectedTab === "completed") return chat.status === "completed" && matchesSearch;
    if (selectedTab === "flagged") return chat.flagged && matchesSearch;
    
    return true;
  });

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800 p-6">
        <h2 className="text-xl font-bold mb-6">MATFix Admin</h2>
        
        <nav className="space-y-1">
          <Button variant="default" className="w-full justify-start mb-1">
            <MessageSquare className="mr-2 h-4 w-4" /> Chat Logs
          </Button>
          <Button variant="ghost" className="w-full justify-start mb-1">
            <Users className="mr-2 h-4 w-4" /> User Management
          </Button>
          <Button variant="ghost" className="w-full justify-start mb-1">
            <AlertTriangle className="mr-2 h-4 w-4" /> Flagged Content
          </Button>
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-800 p-6">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold">Chat Monitoring Dashboard</h1>
            
            <div className="flex items-center space-x-4">
              <Button variant="outline" size="sm" className="hidden md:flex">
                <Calendar className="mr-2 h-4 w-4" />
                Last 7 days
              </Button>
              
              <Button variant="outline" size="sm" className="hidden md:flex">
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
              
              <Avatar>
                <AvatarImage src="https://github.com/shadcn.png" alt="Admin" />
                <AvatarFallback>AD</AvatarFallback>
              </Avatar>
            </div>
          </div>
        </header>
        
        <main className="p-6">
          {/* Stats section */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Active Chats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">2</div>
                <p className="text-xs text-muted-foreground">+10% from yesterday</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Chats Today</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">24</div>
                <p className="text-xs text-muted-foreground">+5% from yesterday</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Avg. Response Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">1.2s</div>
                <p className="text-xs text-muted-foreground">-0.1s from yesterday</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Flagged Messages</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">3</div>
                <p className="text-xs text-muted-foreground">Needs review</p>
              </CardContent>
            </Card>
          </div>
          
          {/* Chat logs section */}
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row justify-between md:items-center">
                <div>
                  <CardTitle>Chat Logs</CardTitle>
                  <CardDescription>Monitor and manage user conversations</CardDescription>
                </div>
                
                <div className="flex items-center mt-4 md:mt-0 gap-2">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input 
                      placeholder="Search chats..." 
                      className="pl-8 w-[200px]" 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  
                  <Button variant="outline" size="icon">
                    <Filter className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              <Tabs 
                defaultValue="all" 
                className="mt-6"
                value={selectedTab}
                onValueChange={setSelectedTab}
              >
                <TabsList>
                  <TabsTrigger value="all">All Chats</TabsTrigger>
                  <TabsTrigger value="active">Active</TabsTrigger>
                  <TabsTrigger value="completed">Completed</TabsTrigger>
                  <TabsTrigger value="flagged">Flagged</TabsTrigger>
                </TabsList>
              </Tabs>
            </CardHeader>
            
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Topic</TableHead>
                    <TableHead className="hidden md:table-cell">Messages</TableHead>
                    <TableHead className="hidden md:table-cell">Duration</TableHead>
                    <TableHead>Last Active</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                
                <TableBody>
                  {filteredChats.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-4 text-muted-foreground">
                        No chat logs found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredChats.map(chat => (
                      <TableRow key={chat.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Avatar className="h-8 w-8">
                              <AvatarImage src={chat.user.avatar} />
                              <AvatarFallback>{chat.user.name.charAt(0)}</AvatarFallback>
                            </Avatar>
                            <div className="hidden md:block">
                              <p className="font-medium text-sm">{chat.user.name}</p>
                              <p className="text-xs text-muted-foreground">{chat.user.email}</p>
                            </div>
                            <p className="md:hidden text-sm">{chat.user.name}</p>
                          </div>
                        </TableCell>
                        
                        <TableCell className="max-w-[150px] truncate">
                          {chat.topic}
                          {chat.flagged && (
                            <Badge variant="outline" className="ml-2 bg-red-100 text-red-800 border-red-200">
                              Flagged
                            </Badge>
                          )}
                        </TableCell>
                        
                        <TableCell className="hidden md:table-cell">
                          {chat.messageCount}
                        </TableCell>
                        
                        <TableCell className="hidden md:table-cell">
                          {chat.duration}
                        </TableCell>
                        
                        <TableCell>
                          {chat.lastActive}
                        </TableCell>
                        
                        <TableCell>
                          <Badge 
                            variant="outline" 
                            className={
                              chat.status === "active" 
                                ? "bg-green-100 text-green-800 border-green-200"
                                : "bg-gray-100 text-gray-800 border-gray-200"
                            }
                          >
                            {chat.status === "active" ? "Active" : "Completed"}
                          </Badge>
                        </TableCell>
                        
                        <TableCell className="text-right">
                          <Button size="sm" variant="ghost">View</Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  );
}