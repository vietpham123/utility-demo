require 'sinatra'
require 'sinatra/json'
require 'json'
require 'securerandom'
require 'digest'
require 'time'

set :bind, '0.0.0.0'
set :port, 4567
set :show_exceptions, false

# ============================================================
# Customer Service (Ruby/Sinatra) — User auth, profiles, search
# Adds Ruby to polyglot mix. Provides login/session for RUM user identification
# ============================================================

# In-memory user/customer store (simulated — like existing services)
USERS = {
  'operator_jones' => { id: 'USR-001', name: 'Sarah Jones', email: 'sjones@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'operator', region: 'Chicago-Metro', preferences: { theme: 'dark', timezone: 'America/Chicago', notifications: { email: true, sms: true, push: true } } },
  'engineer_chen' => { id: 'USR-002', name: 'David Chen', email: 'dchen@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'engineer', region: 'Philadelphia-Metro', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: false, push: true } } },
  'manager_smith' => { id: 'USR-003', name: 'Michael Smith', email: 'msmith@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'manager', region: 'Baltimore-Metro', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: true, push: true } } },
  'analyst_garcia' => { id: 'USR-004', name: 'Maria Garcia', email: 'mgarcia@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'analyst', region: 'DC-Metro', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: false, push: false } } },
  'dispatcher_lee' => { id: 'USR-005', name: 'James Lee', email: 'jlee@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'dispatcher', region: 'Atlantic-Coast', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: true, push: true } } },
  'supervisor_patel' => { id: 'USR-006', name: 'Arun Patel', email: 'apatel@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'supervisor', region: 'Delaware-Valley', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: true, push: true } } },
  'technician_wong' => { id: 'USR-007', name: 'Emily Wong', email: 'ewong@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'technician', region: 'Chicago-Metro', preferences: { theme: 'dark', timezone: 'America/Chicago', notifications: { email: true, sms: true, push: false } } },
  'director_johnson' => { id: 'USR-008', name: 'Robert Johnson', email: 'rjohnson@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'director', region: 'DC-Metro', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: true, push: true } } },
  'operator_brown' => { id: 'USR-009', name: 'Lisa Brown', email: 'lbrown@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'operator', region: 'Baltimore-Metro', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: false, push: true } } },
  'engineer_martinez' => { id: 'USR-010', name: 'Carlos Martinez', email: 'cmartinez@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'engineer', region: 'Philadelphia-Metro', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: true, push: false } } },
  'analyst_taylor' => { id: 'USR-011', name: 'Jessica Taylor', email: 'jtaylor@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'analyst', region: 'Atlantic-Coast', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: false, push: true } } },
  'dispatcher_harris' => { id: 'USR-012', name: 'Kevin Harris', email: 'kharris@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'dispatcher', region: 'Chicago-Metro', preferences: { theme: 'dark', timezone: 'America/Chicago', notifications: { email: true, sms: true, push: true } } },
  'technician_clark' => { id: 'USR-013', name: 'Amanda Clark', email: 'aclark@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'technician', region: 'DC-Metro', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: false, sms: true, push: true } } },
  'manager_lewis' => { id: 'USR-014', name: 'Thomas Lewis', email: 'tlewis@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'manager', region: 'Delaware-Valley', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: false, push: false } } },
  'operator_robinson' => { id: 'USR-015', name: 'Nicole Robinson', email: 'nrobinson@genericutility.com', password_hash: Digest::SHA256.hexdigest(ENV['DEMO_PASSWORD'] || 'utility2026'), role: 'operator', region: 'Baltimore-Metro', preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: true, push: true } } },
}

# Simulated utility customers (the people served, not app users)
CUSTOMERS = (1..200).map do |i|
  regions = ['Chicago-Metro', 'Baltimore-Metro', 'Philadelphia-Metro', 'DC-Metro', 'Atlantic-Coast', 'Delaware-Valley']
  cities = { 'Chicago-Metro' => ['Chicago', 'Evanston', 'Oak Park', 'Naperville'],
             'Baltimore-Metro' => ['Baltimore', 'Towson', 'Columbia', 'Annapolis'],
             'Philadelphia-Metro' => ['Philadelphia', 'Camden', 'Chester', 'Norristown'],
             'DC-Metro' => ['Washington', 'Arlington', 'Bethesda', 'Silver Spring'],
             'Atlantic-Coast' => ['Atlantic City', 'Trenton', 'Newark', 'Cherry Hill'],
             'Delaware-Valley' => ['Wilmington', 'Dover', 'Newark DE', 'New Castle'] }
  region = regions[i % regions.length]
  city = cities[region][i % cities[region].length]
  {
    id: "CUST-#{i.to_s.rjust(4, '0')}",
    accountNumber: "ACC-#{(100000 + i)}",
    name: "Customer #{i}",
    email: "customer#{i}@example.com",
    phone: "(555) #{rand(100..999)}-#{rand(1000..9999)}",
    address: "#{rand(100..9999)} #{['Main', 'Oak', 'Elm', 'Park', 'Cedar', 'Maple', 'Pine'][i % 7]} St",
    city: city,
    state: region.include?('Chicago') ? 'IL' : region.include?('Baltimore') ? 'MD' : region.include?('Philadelphia') ? 'PA' : region.include?('DC') ? 'DC' : region.include?('Atlantic') ? 'NJ' : 'DE',
    region: region,
    serviceType: ['Residential', 'Commercial', 'Industrial'][i % 3],
    meterId: "MTR-#{(1000 + i)}",
    status: i % 20 == 0 ? 'Inactive' : 'Active',
    rateClass: ['R-1', 'R-2', 'C-1', 'C-2', 'I-1'][i % 5],
    monthlyUsageKwh: rand(200..3000),
    registeredAt: (Time.now - rand(1..365) * 86400).iso8601
  }
end

SESSIONS = {}

before do
  content_type :json
  if request.content_type&.include?('application/json') && request.body.size > 0
    request.body.rewind
    @json_body = JSON.parse(request.body.read) rescue {}
  else
    @json_body = {}
  end
end

# ============================================================
# Authentication endpoints
# ============================================================
post '/api/auth/login' do
  username = @json_body['username']
  password = @json_body['password']

  unless username && password
    halt 400, json(error: 'Username and password required')
  end

  user = USERS[username]
  unless user && user[:password_hash] == Digest::SHA256.hexdigest(password)
    halt 401, json(error: 'Invalid credentials')
  end

  token = SecureRandom.hex(32)
  SESSIONS[token] = { user_id: user[:id], username: username, created_at: Time.now.iso8601 }

  puts "AUTH: Login successful for #{username}"
  json(
    token: token,
    user: {
      id: user[:id],
      username: username,
      name: user[:name],
      email: user[:email],
      role: user[:role],
      region: user[:region],
      preferences: user[:preferences]
    }
  )
end

get '/api/auth/users' do
  users_list = USERS.map do |username, user|
    { username: username, name: user[:name], role: user[:role], region: user[:region] }
  end
  json(users: users_list)
end

post '/api/auth/register' do
  username = @json_body['username']
  password = @json_body['password']
  name = @json_body['name']
  email = @json_body['email']
  region = @json_body['region'] || 'Chicago-Metro'

  unless username && password && name && email
    halt 400, json(error: 'Username, password, name, and email required')
  end

  if USERS.key?(username)
    halt 409, json(error: 'Username already exists')
  end

  user_id = "USR-#{USERS.size + 1}"
  USERS[username] = {
    id: user_id, name: name, email: email,
    password_hash: Digest::SHA256.hexdigest(password),
    role: 'viewer', region: region,
    preferences: { theme: 'dark', timezone: 'America/New_York', notifications: { email: true, sms: false, push: false } }
  }

  puts "AUTH: New user registered: #{username}"
  json(status: 'registered', userId: user_id, username: username)
end

post '/api/auth/logout' do
  token = request.env['HTTP_AUTHORIZATION']&.sub('Bearer ', '')
  SESSIONS.delete(token) if token
  json(status: 'logged_out')
end

get '/api/auth/me' do
  token = request.env['HTTP_AUTHORIZATION']&.sub('Bearer ', '')
  session = SESSIONS[token]
  unless session
    halt 401, json(error: 'Not authenticated')
  end
  user = USERS.values.find { |u| u[:id] == session[:user_id] }
  json(user: user&.reject { |k, _| k == :password_hash })
end

# ============================================================
# User preferences
# ============================================================
put '/api/auth/preferences' do
  token = request.env['HTTP_AUTHORIZATION']&.sub('Bearer ', '')
  session = SESSIONS[token]
  unless session
    halt 401, json(error: 'Not authenticated')
  end
  username = session[:username]
  user = USERS[username]
  user[:preferences] = user[:preferences].merge(@json_body.transform_keys(&:to_sym))
  json(status: 'updated', preferences: user[:preferences])
end

# ============================================================
# Customer management endpoints (utility customers, not app users)
# ============================================================
get '/api/customers' do
  page = (params['page'] || 1).to_i
  limit = (params['limit'] || 20).to_i
  offset = (page - 1) * limit

  results = CUSTOMERS[offset, limit] || []
  json(
    customers: results,
    total: CUSTOMERS.length,
    page: page,
    limit: limit,
    totalPages: (CUSTOMERS.length.to_f / limit).ceil
  )
end

get '/api/customers/search' do
  q = (params['q'] || '').downcase
  halt 400, json(error: 'Query parameter q required') if q.empty?

  results = CUSTOMERS.select do |c|
    c[:name].downcase.include?(q) ||
    c[:accountNumber].downcase.include?(q) ||
    c[:address].downcase.include?(q) ||
    c[:city].downcase.include?(q) ||
    c[:meterId].downcase.include?(q) ||
    c[:id].downcase.include?(q)
  end.first(20)

  json(results: results, total: results.length, query: q)
end

get '/api/customers/stats' do
  by_region = CUSTOMERS.group_by { |c| c[:region] }.transform_values(&:length)
  by_type = CUSTOMERS.group_by { |c| c[:serviceType] }.transform_values(&:length)
  active = CUSTOMERS.count { |c| c[:status] == 'Active' }

  json(
    totalCustomers: CUSTOMERS.length,
    activeCustomers: active,
    inactiveCustomers: CUSTOMERS.length - active,
    byRegion: by_region,
    byServiceType: by_type,
    avgMonthlyUsageKwh: (CUSTOMERS.sum { |c| c[:monthlyUsageKwh] }.to_f / CUSTOMERS.length).round(1)
  )
end

get '/api/customers/region/:region' do
  region = params['region']
  results = CUSTOMERS.select { |c| c[:region].downcase.include?(region.downcase) }
  json(
    region: region,
    customers: results.first(50),
    total: results.length
  )
end

get '/api/customers/:id' do
  customer = CUSTOMERS.find { |c| c[:id] == params['id'] || c[:accountNumber] == params['id'] }
  halt 404, json(error: 'Customer not found') unless customer
  json(customer)
end

# Health check
get '/api/customers/health' do
  json(status: 'Healthy', service: 'customer-service', language: 'Ruby', timestamp: Time.now.iso8601)
end

puts "Customer Service (Ruby/Sinatra) starting on port 4567..."
