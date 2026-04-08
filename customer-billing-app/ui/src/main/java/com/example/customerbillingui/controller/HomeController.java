package com.example.customerbillingui.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.client.RestTemplate;
import java.util.List;
import java.util.Map;

@Controller
public class HomeController {
    @GetMapping("/")
    public String index(Model model) {
        RestTemplate restTemplate = new RestTemplate();
        List customers = restTemplate.getForObject("http://localhost:5000/api/customer", List.class);
        model.addAttribute("customers", customers);
        return "index";
    }
}
